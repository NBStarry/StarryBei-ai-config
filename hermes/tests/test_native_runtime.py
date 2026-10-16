"""在目标 Hermes 虚拟环境运行；使用真实插件发现和工具分发，不调用模型。"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]


@unittest.skipUnless(os.environ.get('HERMES_SOURCE'), '需要目标 Hermes 源码和虚拟环境')
class NativeRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='workflow-native-')
        cls.root = Path(cls.temp.name).resolve() / 'project'
        cls.root.mkdir()
        cls.home = cls.root.parent / 'hermes-home'
        cls.old_env = dict(os.environ)
        os.environ.update(HERMES_HOME=str(cls.home), TERMINAL_CWD=str(cls.root), TERMINAL_ENV='local')
        sys.path.insert(0, os.environ['HERMES_SOURCE'])
        subprocess.run(['git', 'init', '-q', str(cls.root)], check=True)
        (cls.root / 'src').mkdir()
        (cls.root / 'agent-coops').mkdir()
        workflow = REPO / 'workflow/v0.1.0/workflow.py'
        config = dict(workflow_version='0.1.0', workflow_source=str(workflow.parent),
                      workflow_sha256=hashlib.sha256(workflow.read_bytes()).hexdigest(),
                      root_files=['STATUS.md'], allowed_roots=['src', 'agent-coops'])
        cls.config_path = cls.root / 'agent-coops/project.json'
        cls.config_path.write_text(json.dumps(config))
        spec = importlib.util.spec_from_file_location('native_installer', REPO / 'scripts/install-workflow.py')
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        installer.install('hermes', cls.home)
        from hermes_cli.plugins import get_plugin_manager
        cls.manager = get_plugin_manager()
        cls.manager.discover_and_load()
        from tools.terminal_tool import record_session_cwd
        record_session_cwd('native-workflow-probe', str(cls.root))
        # 工具注册走 Hermes 本身；测试不手工调用适配器回调。
        import tools.file_tools
        from model_tools import handle_function_call
        cls.dispatch = staticmethod(handle_function_call)

    @classmethod
    def tearDownClass(cls):
        os.environ.clear()
        os.environ.update(cls.old_env)
        cls.temp.cleanup()

    def call(self, name, args):
        return self.dispatch(name, args, task_id='native-workflow-probe',
                             session_id='native-workflow-probe', tool_call_id='probe-' + self.id())

    def test_01_native_discovery_and_context(self):
        self.assertTrue(self.manager._middleware.get('tool_execution'))
        from hermes_cli.lifecycle import invoke_hook
        values = invoke_hook('pre_llm_call', session_id='native-workflow-probe',
                             task_id='native-workflow-probe')
        self.assertTrue(any('同一目标' in str(value) for value in values), values)

    def test_02_actual_write_and_replace(self):
        result = self.call('write_file', {'path': 'src/native.txt', 'content': 'native OK\n'})
        self.assertTrue((self.root / 'src/native.txt').exists(), result)
        self.assertNotIn('HOOK_CHANGED', result)
        self.call('read_file', {'path': 'src/native.txt'})
        result = self.call('patch', {'path': 'src/native.txt', 'old_string': 'native OK', 'new_string': 'native PATCH'})
        self.assertEqual((self.root / 'src/native.txt').read_text(), 'native PATCH\n', result)

    def test_03_actual_tool_is_blocked(self):
        result = self.call('write_file', {'path': 'native-denied.txt', 'content': 'must not exist\n'})
        self.assertIn('PATH_DENIED', result)
        self.assertFalse((self.root / 'native-denied.txt').exists())

    def test_03_v4a_external_path_and_native_move(self):
        from tools.terminal_tool import record_session_cwd
        record_session_cwd('native-workflow-probe', str(self.root.parent))
        try:
            result = self.call('patch', {'mode': 'patch', 'patch':
                '*** Begin Patch\n***Add File: ' + str(self.root / 'v4a-denied.txt') + '\n+no\n*** End Patch\n'})
            self.assertIn('PATH_DENIED', result)
            self.assertFalse((self.root / 'v4a-denied.txt').exists())
        finally:
            record_session_cwd('native-workflow-probe', str(self.root))
        self.call('read_file', {'path': 'src/native.txt'})
        result = self.call('patch', {'mode': 'patch', 'patch':
            '*** Begin Patch\n*** Move File: src/native.txt -> src/moved.txt\n*** End Patch\n'})
        self.assertTrue((self.root / 'src/moved.txt').exists(), result)
        self.assertNotIn('HOOK_CHANGED', result)

    def test_04_finish_and_unconfigured_project(self):
        from hermes_cli.lifecycle import invoke_hook
        values = invoke_hook('pre_verify', session_id='native-workflow-probe')
        self.assertFalse(any(isinstance(v, dict) and v.get('action') == 'continue' for v in values), values)
        self.config_path.rename(self.config_path.with_suffix('.disabled'))
        result = self.call('write_file', {'path': 'native-unconfigured.txt', 'content': 'allowed\n'})
        self.assertTrue((self.root / 'native-unconfigured.txt').exists(), result)


if __name__ == '__main__':
    unittest.main()
