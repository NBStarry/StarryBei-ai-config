import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('workflow_install', REPO / 'scripts/install-workflow.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)

    def test_codex_preserves_hooks_is_idempotent_and_rolls_back_exactly(self):
        path = self.home / 'hooks.json'
        original = '{"hooks":{"Stop":[{"hooks":[{"type":"command","command":"other-hook"}]}]}}\n'
        path.write_text(original)
        (self.home / 'AGENTS.md').write_text('personal rules\n')
        before = {p: installer.snapshot(p) for p in (path, self.home / 'AGENTS.md')}
        receipt = installer.install('codex', self.home)
        self.assertEqual(json.loads(path.read_text())['hooks']['Stop'][0]['hooks'][0]['command'], 'other-hook')
        self.assertIsNone(installer.install('codex', self.home))
        installer.rollback(receipt)
        for p, value in before.items():
            self.assertEqual(installer.snapshot(p), value)
        self.assertFalse((self.home / 'hooks/workflow-hook.py').exists())

    def test_rollback_refuses_later_edits_without_partial_restore(self):
        receipt = installer.install('codex', self.home)
        (self.home / 'hooks.json').write_text('{"later":true}')
        with self.assertRaisesRegex(ValueError, '已变化'):
            installer.rollback(receipt)
        self.assertTrue((self.home / 'AGENTS.md').is_symlink())

    def test_conflicting_hook_fails_before_any_write(self):
        (self.home / 'hooks.json').write_text(json.dumps({'hooks': {'Stop': [{'hooks': [
            {'command': 'python3 other/workflow-hook.py'}]}]}}))
        with self.assertRaisesRegex(ValueError, '不同'):
            installer.install('codex', self.home)
        self.assertFalse((self.home / 'AGENTS.md').exists())

    def test_failed_link_restores_already_written_targets(self):
        (self.home / 'AGENTS.md').write_text('keep me')
        real = installer.restore
        def fail(path, state):
            if path.name == 'workflow-hook.py' and state is not None:
                raise OSError('no symlink permission')
            real(path, state)
        with patch.object(installer, 'restore', side_effect=fail):
            with self.assertRaises(OSError):
                installer.install('codex', self.home)
        self.assertEqual((self.home / 'AGENTS.md').read_text(), 'keep me')

    def test_narrow_matcher_is_not_mistaken_for_complete_installation(self):
        installer.install('codex', self.home)
        path = self.home / 'hooks.json'
        data = json.loads(path.read_text())
        data['hooks']['PreToolUse'][0]['matcher'] = 'Read'
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, '不同'):
            installer.install('codex', self.home)

    def test_hermes_preserves_config_rules_and_round_trips(self):
        import yaml
        path = self.home / 'config.yaml'
        original = '# keep original on rollback\nmodel: test\nplugins:\n  enabled: [existing]\n'
        path.write_text(original)
        (self.home / 'AGENTS.md').write_text('team rules')
        receipt = installer.install('hermes', self.home)
        self.assertEqual(yaml.safe_load(path.read_text())['plugins']['enabled'], ['existing', installer.PLUGIN])
        self.assertEqual((self.home / 'AGENTS.md').read_text(), 'team rules')
        self.assertIsNone(installer.install('hermes', self.home))
        installer.rollback(receipt)
        self.assertEqual(path.read_text(), original)


if __name__ == '__main__':
    unittest.main()
