"""隔离样例验证权限、候选树和真实 Git pre-commit；不访问用户配置。"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'workflow.py'
spec = importlib.util.spec_from_file_location('workflow', SCRIPT)
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
PLAN = '# 测试\n\n## 目标与范围\n仅测试。\n\n## 计划与进展\n- [ ] S1 检查结果\n\n## 阻塞与决策\n无。\n\n## 验收与证据\n命令返回预期结果。\n'


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='workflow-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Workflow Test')
        self.config = {'workflow_version': '0.1.0', 'root_files': ['STATUS.md', 'README.md'], 'allowed_roots': ['agent-coops', 'src']}
        self.put('agent-coops/project.json', json.dumps(self.config))
        self.path = 'agent-coops/tasks/测试/计划.md'
        self.record_path = 'agent-coops/tasks/测试/执行记录.md'
        self.record = '# 测试记录\n\n## 目标与范围\n[计划](计划.md)\nhttps://applink.feishu.cn/client/todo/detail?guid=test-id\n计划版本：' + w.digest(w.body(PLAN)) + '\n\n## 计划与进展\n已核对。\n\n## 阻塞与决策\n无。\n\n## 验收与证据\n尚未验证。\n'
        self.put(self.record_path, self.record)
        self.put('STATUS.md', '# 状态\n[记录](' + self.record_path + ')\n')
        self.put('draft.md', PLAN)
        self.cli('bind', '--session', 'planner', '--role', 'planner', '--task', '测试')
        self.cli('bind', '--session', 'executor', '--role', 'executor', '--task', '测试')
        self.cli('publish', '--session', 'planner', '--task', '测试', '--source', str(self.root/'draft.md'), '--reason', '初始化')
        self.git('add', 'STATUS.md', 'agent-coops')
        self.git('commit', '-qm', 'Initial fixture')

    def put(self, path, text):
        dest = self.root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)

    def cli(self, *args, code=0):
        env = {k: v for k, v in os.environ.items() if k not in {'CODEX_THREAD_ID', 'CLAUDE_SESSION_ID'}}
        p = subprocess.run([sys.executable, '-B', str(SCRIPT), '--root', str(self.root), *args], capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, code, p.stdout + p.stderr)
        return p

    def event(self, tool='Write', data=None, session='executor', phase='PreToolUse'):
        return {'hook_event_name': phase, 'session_id': session, 'cwd': str(self.root), 'tool_name': tool, 'tool_input': data or {}}

    def test_executor_cannot_rewrite_or_delete_plan(self):
        for text in [PLAN.replace('仅测试', '扩大范围'), PLAN.replace('S1 检查结果', 'S1 不检查')]:
            errors = w.hook(self.root, self.config, self.event(data={'file_path': self.path, 'content': text}))
            self.assertIn('PLAN_IMMUTABLE', ' '.join(errors))
        errors = w.hook(self.root, self.config, self.event('apply_patch', {'command': '*** Begin Patch\n*** Delete File: '+self.path+'\n*** End Patch\n'}))
        self.assertIn('PLAN_IMMUTABLE', ' '.join(errors))

    def test_checkbox_requires_evidence_and_keeps_version(self):
        changed = PLAN.replace('[ ]', '[x]')
        event = self.event(data={'file_path': self.path, 'content': changed})
        self.assertIn('PLAN_EVIDENCE', ' '.join(w.hook(self.root, self.config, event)))
        self.put(self.record_path, self.record + '- 证据 S1：2026-10-13，隔离命令通过。\n')
        self.assertEqual(w.hook(self.root, self.config, event), [])
        self.put(self.path, changed)
        self.assertEqual(w.hook(self.root, self.config, self.event(phase='PostToolUse')), [])
        event['tool_input']['content'] = PLAN
        self.assertIn('PLAN_UNCHECK', ' '.join(w.hook(self.root, self.config, event)))

    def test_planner_publication_and_record_version(self):
        updated = PLAN.replace('仅测试。', '仅测试修订。')
        self.put('draft.md', updated)
        self.cli('publish', '--session', 'executor', '--task', '测试', '--source', str(self.root/'draft.md'), '--reason', '越权', code=2)
        self.cli('publish', '--session', 'planner', '--task', '测试', '--source', str(self.root/'draft.md'), '--reason', '授权内修订')
        self.assertTrue(list((w.state_dir(self.root)/'history').glob('*.md')))
        self.assertIn('PLAN_VERSION', self.cli('check', self.path, code=2).stderr)
        self.put(self.record_path, self.record.replace(w.digest(w.body(PLAN)), w.digest(w.body(updated))))
        self.cli('check', self.path)

    def test_role_is_not_self_declared_or_rebound(self):
        event = self.event(data={'file_path': self.path, 'content': PLAN+'新正文\n'})
        event['role'] = 'planner'
        self.assertTrue(w.hook(self.root, self.config, event))
        self.cli('bind', '--session', 'executor', '--role', 'planner', '--task', '测试', code=2)
        errors = w.hook(self.root, self.config, self.event('Bash', {'command': 'python3 agent-coops/run.py bind --role planner'}))
        self.assertIn('ROLE_DENIED', ' '.join(errors))

    def test_other_task_and_duplicate_plan_are_rejected(self):
        errors = w.hook(self.root, self.config, self.event(data={'file_path':'agent-coops/tasks/其他/执行记录.md','content':self.record}))
        self.assertIn('TASK_OWNER', ' '.join(errors))
        self.put('agent-coops/tasks/测试/计划二.md', PLAN)
        self.assertIn('TASK_LAYOUT', self.cli('check','agent-coops/tasks/测试/计划二.md',code=2).stderr)

    def test_bad_directory_link_and_symlink(self):
        self.put('random.md', 'wrong directory')
        self.assertIn('PATH_DENIED', self.cli('check','random.md',code=2).stderr)
        self.put('STATUS.md','# 状态\n[缺失](missing.md)\n')
        self.assertIn('LINK_MISSING', self.cli('check','STATUS.md',code=2).stderr)
        (self.root/'src').mkdir()
        (self.root/'src/escape').symlink_to('/tmp')
        with self.assertRaises(ValueError):
            w.checked_path(self.root,'src/escape/abc')

    def test_staged_tree_does_not_use_worktree_repair(self):
        self.put(self.path, PLAN.replace('仅测试。','偷偷改计划。'))
        self.git('add', self.path)
        self.put(self.path, PLAN)
        self.assertIn('PLAN_UNPUBLISHED', self.cli('check','--staged',code=2).stderr)

    def test_unrelated_dirty_file_does_not_block(self):
        self.put('other-owner.md','invalid historical content')
        self.put('src/good.py','print(1)\n')
        self.git('add','src/good.py')
        self.cli('check','--staged')

    def test_process_actor_cannot_spoof_planner(self):
        args = [sys.executable, str(SCRIPT), '--root', str(self.root), 'publish', '--session', 'planner', '--task', '测试', '--source', str(self.root/'draft.md'), '--reason', 'spoof']
        p = subprocess.run(args, capture_output=True, text=True, env={**os.environ, 'CODEX_THREAD_ID': 'executor'})
        self.assertEqual(p.returncode,2)
        self.assertIn('ROLE_ACTOR',p.stderr)

    def test_completion_without_steps_and_legacy_new_file(self):
        self.put(self.record_path,self.record+'工程结论：已完成\n')
        self.assertIn('TASK_INCOMPLETE',self.cli('check',self.record_path,code=2).stderr)
        self.config['legacy_task_roots']=['src/old-plans']
        self.put('agent-coops/project.json',json.dumps(self.config))
        self.put('src/old-plans/new.md',PLAN)
        self.assertIn('TASK_LEGACY',self.cli('check','src/old-plans/new.md',code=2).stderr)

    def test_git_precommit_blocks_real_commit(self):
        hook = self.root/'.git/hooks/pre-commit'
        hook.write_text('#!/bin/sh\nexec '+sys.executable+' '+str(SCRIPT)+' --root "'+str(self.root)+'" check --staged\n')
        hook.chmod(0o755)
        self.put(self.path, PLAN.replace('命令返回预期结果','无需验收'))
        self.git('add', self.path)
        p = subprocess.run(['git','-C',str(self.root),'commit','-m','Should fail'],capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0)
        self.assertIn('PLAN_UNPUBLISHED',p.stderr)

    def test_patch_edit_and_post_external_change(self):
        patch='*** Begin Patch\n*** Update File: '+self.record_path+'\n@@\n-已核对。\n+已核对入口。\n*** End Patch\n'
        event=self.event('apply_patch',{'command':patch})
        self.assertEqual(w.hook(self.root,self.config,event),[])
        self.put(self.record_path,self.record.replace('已核对。','另一执行者改动。'))
        errors=w.hook(self.root,self.config,self.event(phase='PostToolUse'))
        self.assertIn('HOOK_CHANGED',' '.join(errors))
        self.assertIn('另一执行者',w.read(self.root/self.record_path))


if __name__ == '__main__':
    unittest.main()
