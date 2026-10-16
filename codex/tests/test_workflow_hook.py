import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
HOOK = REPO / 'codex/hooks/workflow-hook.py'
WORKFLOW = REPO / 'workflow/v0.1.0/workflow.py'


class GlobalHookTests(unittest.TestCase):
    workflow = WORKFLOW
    version = "0.1.0"
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)

    def configure(self, **changes):
        config = dict(workflow_version=self.version, workflow_source=str(self.workflow.parent),
                      workflow_sha256=hashlib.sha256(self.workflow.read_bytes()).hexdigest(),
                      root_files=['STATUS.md'], allowed_roots=['src', 'agent-coops'])
        config.update(changes)
        path = self.root / 'agent-coops/project.json'
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(config))

    def call(self, phase='PreToolUse', cwd=None, data=None):
        event = dict(hook_event_name=phase, cwd=str(cwd or self.root), session_id='test-session',
                     tool_name='apply_patch', tool_input=data or {'command':
                     '*** Begin Patch\n*** Add File: unexpected.txt\n+no\n*** End Patch\n'})
        return subprocess.run([sys.executable, '-B', str(HOOK)], input=json.dumps(event),
                              capture_output=True, text=True)

    def test_unconfigured_repo_is_explicit_and_unchanged(self):
        result = self.call('SessionStart')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('未接入', json.loads(result.stdout)['hookSpecificOutput']['additionalContext'])
        self.assertEqual(self.call().returncode, 0)
        self.assertFalse((self.root / 'agent-coops').exists())

    def test_out_of_scope_patch_is_blocked_from_subdirectory(self):
        self.configure()
        child = self.root / 'src'; child.mkdir()
        result = self.call(cwd=child, data={'command':
            '*** Begin Patch\n*** Add File: ../unexpected.txt\n+no\n*** End Patch\n'})
        self.assertEqual(result.returncode, 2)
        self.assertIn('PATH_DENIED', result.stderr)
        self.assertFalse((self.root / 'unexpected.txt').exists())

    def test_expected_patch_and_post_check(self):
        self.configure()
        (self.root / 'src').mkdir()
        data = {'command': '*** Begin Patch\n*** Add File: src/ok.txt\n+ok\n*** End Patch\n'}
        self.assertEqual(self.call(data=data).returncode, 0)
        (self.root / 'src/ok.txt').write_text('ok\n')
        self.assertEqual(self.call('PostToolUse', data=data).returncode, 0)
        self.assertEqual(self.call('Stop').returncode, 0)

    def test_changed_output_is_reported_without_reverting(self):
        self.configure()
        (self.root / 'src').mkdir()
        data = {'command': '*** Begin Patch\n*** Add File: src/ok.txt\n+ok\n*** End Patch\n'}
        self.assertEqual(self.call(data=data).returncode, 0)
        path = self.root / 'src/ok.txt'; path.write_text('another owner\n')
        result = self.call('PostToolUse', data=data)
        self.assertEqual(result.returncode, 2)
        self.assertIn('HOOK_CHANGED', result.stderr)
        self.assertEqual(path.read_text(), 'another owner\n')

    def test_pin_and_source_are_checked_before_execution(self):
        for changes, error in [({'workflow_sha256': 'wrong'}, 'WORKFLOW_PIN'),
                               ({'workflow_source': '/tmp/untrusted'}, 'WORKFLOW_SOURCE'),
                               ({'workflow_version': '../escape'}, 'WORKFLOW_VERSION')]:
            with self.subTest(changes=changes):
                self.configure(**changes)
                result = self.call()
                self.assertEqual(result.returncode, 2)
                self.assertIn(error, result.stderr)

    def test_nested_independent_repo_does_not_inherit_parent_policy(self):
        self.configure()
        child = self.root / 'independent'; child.mkdir()
        subprocess.run(['git', 'init', '-q', str(child)], check=True)
        self.assertEqual(self.call(cwd=child).returncode, 0)
        self.assertFalse((child / '.git/agent-coops').exists())

    def test_project_runner_is_never_executed(self):
        self.configure()
        (self.root / 'agent-coops/run.py').write_text('raise RuntimeError("untrusted")')
        result = self.call('SessionStart')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(self.version, json.loads(result.stdout)['hookSpecificOutput']['additionalContext'])


class SelfBindingHookTests(GlobalHookTests):
    workflow = REPO / "workflow/v0.1.1/workflow.py"
    version = "0.1.1"


if __name__ == '__main__':
    unittest.main()
