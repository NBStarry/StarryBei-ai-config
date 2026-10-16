from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import subprocess
import tempfile
import time
import types
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
WORKFLOW = REPO / 'workflow/v0.1.0/workflow.py'
spec = importlib.util.spec_from_file_location('hermes_workflow', REPO / 'hermes/workflow-plugin/__init__.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class HermesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.root / 'src').mkdir()
        (self.root / 'agent-coops').mkdir()
        self.config = dict(workflow_version='0.1.0', workflow_source=str(WORKFLOW.parent),
                           workflow_sha256=hashlib.sha256(WORKFLOW.read_bytes()).hexdigest(),
                           root_files=['STATUS.md'], allowed_roots=['src', 'agent-coops'])
        (self.root / 'agent-coops/project.json').write_text(json.dumps(self.config))
        paths = types.ModuleType('tools.file_tools_paths')
        paths._resolve_base_dir = lambda task: self.root
        paths._terminal_env_type_for_task = lambda task: 'local'
        paths._resolve_path_for_task = lambda p, task: (self.root / p).resolve()
        files = types.ModuleType('tools.file_tools')
        def collect(patch_text):
            paths = re.findall(r'^\*\*\*\s*(?:Add|Update|Delete)\s+File:\s*(.+)$', patch_text, re.M)
            for old, new in re.findall(r'^\*\*\*\s*Move\s+File:\s*(.+?)\s*->\s*(.+)$', patch_text, re.M):
                paths += [old, new]
            return paths, paths
        files._collect_v4a_header_paths = collect
        self.patcher = patch.dict('sys.modules', {'tools.file_tools_paths': paths, 'tools.file_tools': files})
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        adapter._sessions.clear()

    def write(self, path='src/ok.txt', content='ok\n', **kwargs):
        def actual(args):
            (self.root / args['path']).write_text(args['content'])
            return 'written'
        return adapter.execute('write_file', {'path': path, 'content': content},
                               kwargs.pop('next_call', actual), session_id='test', task_id='test', **kwargs)

    def test_allowed_write_post_and_finish(self):
        self.assertEqual(self.write(), 'written')
        self.assertIsNone(adapter.finish(session_id='test'))
        events = [json.loads(s)['event'] for s in (self.root / '.git/agent-coops/events.jsonl').read_text().splitlines()]
        self.assertEqual(events, ['PreToolUse', 'PostToolUse', 'Stop'])

    def test_out_of_scope_is_blocked_before_actual_tool(self):
        self.assertIn('PATH_DENIED', self.write('unexpected.txt'))
        self.assertFalse((self.root / 'unexpected.txt').exists())

    def test_wrong_output_is_reported_and_not_reverted(self):
        def actual(args):
            (self.root / args['path']).write_text('other actor\n')
            return 'done'
        self.assertIn('HOOK_CHANGED', self.write(next_call=actual))
        self.assertEqual((self.root / 'src/ok.txt').read_text(), 'other actor\n')
        self.assertEqual(adapter.finish(session_id='test')['action'], 'continue')

    def test_concurrent_writes_do_not_overwrite_pending(self):
        def actual(args):
            time.sleep(0.02)
            (self.root / args['path']).write_text(args['content'])
            return 'written'
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda name: self.write('src/' + name, next_call=actual), ['a', 'b']))
        self.assertEqual(results, ['written', 'written'])
        self.assertIsNone(adapter.finish(session_id='test'))

    def test_unconfigured_project_keeps_existing_behavior(self):
        (self.root / 'agent-coops/project.json').unlink()
        self.assertEqual(self.write('unexpected.txt'), 'written')
        self.assertFalse((self.root / '.git/agent-coops').exists())

    def test_fixed_source_failure_blocks_and_context_is_loaded(self):
        self.assertIn('同一目标', adapter.context(session_id='test', task_id='test')['context'])
        self.config['workflow_sha256'] = 'wrong'
        (self.root / 'agent-coops/project.json').write_text(json.dumps(self.config))
        self.assertIn('WORKFLOW_PIN', self.write())
        self.assertFalse((self.root / 'src/ok.txt').exists())

    def test_patch_replace_uses_same_protection(self):
        (self.root / 'src/ok.txt').write_text('old\n')
        def actual(args):
            (self.root / args['path']).write_text('new\n')
            return 'patched'
        result = adapter.execute('patch', dict(path='src/ok.txt', old_string='old', new_string='new'),
                                 actual, session_id='test', task_id='test')
        self.assertEqual(result, 'patched')

    def test_v4a_patch_from_outside_cannot_skip_target_policy(self):
        for header in ('*** Add File: ', '***Add File: '):
            with patch.object(adapter, 'workspace', return_value=self.root.parent):
                result = adapter.execute('patch', {'mode': 'patch', 'patch':
                    '*** Begin Patch\n' + header + str(self.root / 'denied.txt') + '\n+no\n*** End Patch\n'},
                    lambda args: self.fail('must not execute'), session_id='test', task_id='test')
            self.assertIn('PATH_DENIED', result)

    def test_native_move_checks_both_paths(self):
        (self.root / 'src/old.txt').write_text('keep\n')
        result = adapter.execute('patch', {'mode': 'patch', 'patch':
            '*** Begin Patch\n***Move File: src/old.txt -> denied.txt\n*** End Patch\n'},
            lambda args: self.fail('must not execute'), session_id='test', task_id='test')
        self.assertIn('PATH_DENIED', result)

    def test_executor_cannot_change_plan_or_bind_itself(self):
        task = self.root / 'agent-coops/tasks/probe'
        task.mkdir(parents=True)
        (task / '计划.md').write_text('original plan')
        state = self.root / '.git/agent-coops'
        state.mkdir()
        (state / 'roles.json').write_text(json.dumps({'test': {'role': 'executor', 'task': 'probe'}}))
        self.assertIn('PLAN_IMMUTABLE', self.write('agent-coops/tasks/probe/计划.md', 'changed'))
        result = adapter.execute('terminal', {'command': 'python3 agent-coops/run.py bind --session test --role planner'},
                                 lambda args: self.fail('must not execute'), session_id='test', task_id='test')
        self.assertIn('ROLE_DENIED', result)


if __name__ == '__main__':
    unittest.main()
