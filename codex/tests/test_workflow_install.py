"""基础安装与团队兼容入口：全部写入只发生在临时 HOME。"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]


def snapshot(root):
    return {str(p.relative_to(root)): ('link', os.readlink(p)) if p.is_symlink()
            else ('file', p.read_bytes(), p.stat().st_mode) if p.is_file()
            else ('dir',) for p in root.rglob('*')}


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home),
                        HERMES_HOME=str(self.home / '.hermes'))

    def run_command(self, command):
        result = subprocess.run(command, cwd=REPO, env=self.env, text=True,
                                capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return result.stdout

    def seed_team(self):
        for name, content in {
            '.codex/hooks.json': '{"hooks":{"Stop":[{"hooks":[{"command":"existing-team-hook"}]}]}}',
            '.codex/hooks/workflow-hook.py': '# existing team hook',
            '.hermes/config.yaml': 'model: existing\nplugins:\n  enabled: [starrybei-workflow]\n',
            '.hermes/plugins/starrybei-workflow/__init__.py': '# existing team plugin',
            '.hermes/AGENTS.md': 'existing profile rules',
        }.items():
            path = self.home / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        (self.home / '.codex/workflow-sources.json').symlink_to('existing-sources.json')

    def test_legacy_python_install_and_rollback_do_not_touch_home(self):
        self.seed_team()
        receipt = self.home / 'receipt.json'
        receipt.write_text('{"changes": []}')
        before = snapshot(self.home)
        for arguments in [
            ['--tool', 'codex', '--home', str(self.home / 'new-codex')],
            ['--tool', 'hermes', '--home', str(self.home / 'new-hermes')],
            ['--rollback', str(receipt)],
        ]:
            with self.subTest(arguments=arguments):
                output = self.run_command([sys.executable, '-B', 'scripts/install-workflow.py', *arguments])
                self.assertIn('https://github.com/NBStarry/SuperBeiTeam', output)
                self.assertIn('未修改任何配置', output)
                self.assertEqual(snapshot(self.home), before)

    def test_bash_workflow_only_is_a_noop(self):
        self.seed_team()
        before = snapshot(self.home)
        output = self.run_command(['bash', 'install.sh', '--workflow-only'])
        self.assertIn('SuperBeiTeam', output)
        self.assertIn('私有仓库', output)
        self.assertEqual(snapshot(self.home), before)

    @unittest.skipUnless(shutil.which('pwsh'), '未安装 PowerShell；Windows 实机另验')
    def test_powershell_workflow_only_is_a_noop(self):
        self.seed_team()
        before = snapshot(self.home)
        output = self.run_command(['pwsh', '-NoProfile', '-File', 'install.ps1', '-WorkflowOnly'])
        self.assertIn('SuperBeiTeam', output)
        self.assertEqual(snapshot(self.home), before)

    def test_base_install_links_principles_without_installing_or_removing_team(self):
        # CLI 探测使用无操作 fixture；不运行真实工具或插件市场。
        binaries = self.home / 'bin'
        binaries.mkdir()
        for name in ('claude', 'codex'):
            path = binaries / name
            path.write_text('#!/bin/sh\nexit 0\n')
            path.chmod(0o755)
        self.env['PATH'] = str(binaries) + os.pathsep + '/usr/bin:/bin:/usr/sbin:/sbin'
        self.run_command(['/bin/bash', 'install.sh', '--skip-skill-plugins'])
        self.assertEqual((self.home / '.codex/AGENTS.md').resolve(), REPO / 'codex/AGENTS.md')
        self.assertFalse((self.home / '.codex/hooks.json').exists())
        self.assertFalse((self.home / '.codex/hooks').exists())
        self.assertFalse((self.home / '.hermes').exists())
        self.seed_team()
        before = snapshot(self.home)
        protected = {p: v for p, v in before.items()
                     if p.startswith('.hermes') or p.startswith('.codex/hooks')
                     or p == '.codex/workflow-sources.json'}
        self.run_command(['/bin/bash', 'install.sh', '--skip-skill-plugins'])
        after = snapshot(self.home)
        self.assertEqual({p: after[p] for p in protected}, protected)
        self.assertEqual((self.home / '.codex/AGENTS.md').resolve(), REPO / 'codex/AGENTS.md')

    def test_manifest_manages_base_principles_only(self):
        resources = json.loads((REPO / 'config/manifest.json').read_text())['resources']
        self.assertEqual([r['source'] for r in resources if r['id'] == 'codex.instructions'], ['codex/AGENTS.md'])
        self.assertFalse(any('workflow' in r['id'] or r['tool'] == 'hermes' for r in resources))

    def test_installers_have_no_team_install_call(self):
        for name in ('install.sh', 'install.ps1'):
            text = (REPO / name).read_text(encoding='utf-8-sig')
            self.assertNotIn('install-workflow.py', text)
            self.assertNotIn('Install-Workflow', text)
            self.assertNotIn('install_workflow', text)
        powershell = (REPO / 'install.ps1').read_text(encoding='utf-8-sig')
        self.assertIn("Link-File (Join-Path $Repo 'codex\\AGENTS.md') (Join-Path $CodexHome 'AGENTS.md')", powershell)


if __name__ == '__main__':
    unittest.main()
