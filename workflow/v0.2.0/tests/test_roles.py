"""五角色流程的隔离 CLI 测试；不调用模型、消息渠道或真实项目。"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'workflow.py'
DESIGN = '''# 隔离任务

## 产品设计
小改动也展示修改前后。

## 架构设计
修改 src/a.py 和 src/b.py，不增加外部依赖。

## 验收设计
A1 返回正确结果。A2 保留另一功能。

## 实施安排
- [ ] S1 实现 A1
- [ ] S2 实现 A2
'''
REPORT = '''# 独立测试

## 目标与范围
按指定产品和架构版本测试 A1、A2。

## 计划与进展
执行真实隔离断言。

## 阻塞与决策
按清单保留未解决问题。

## 验收与证据
测试命令、结果及局限见清单。
'''


class RoleWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='five-role-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.task = '隔离任务'
        self.task_path = 'agent-coops/tasks/' + self.task
        self.ids = {role: 'host-' + role for role in
                    ('coordinator', 'product', 'architect', 'developer', 'tester')}
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Workflow Test')
        self.put('agent-coops/project.json', json.dumps({
            'workflow_version': '0.2.0', 'root_files': ['STATUS.md'],
            'allowed_roots': ['agent-coops', 'src']}))
        self.put('STATUS.md', '# 状态\n[任务记录](' + self.task_path + '/执行记录.md)\n')
        self.put('src/a.py', 'answer = 1\n')
        self.put('src/b.py', 'answer = 2\n')
        self.assets = self.task_path + '/evidence/'
        self.put(self.assets + 'prototype.html', '<link rel="stylesheet" href="ui.css"><script src="ui.js"></script><p>修改前后</p>')
        self.put(self.assets + 'ui.css', '@import "colors.css"; p { color: var(--text); }')
        self.put(self.assets + 'colors.css', ':root { --text: black; }')
        self.put(self.assets + 'ui.js', 'document.title = "修改前后";')
        self.put(self.assets + 'architecture.mmd', 'flowchart LR\n  A[修改前] --> B[修改后]\n')
        self.product_manifest = {
            'assets': [self.assets + 'prototype.html'],
            'criteria': [{'id': 'A1', 'text': '返回正确结果'}, {'id': 'A2', 'text': '保留另一功能'}]}
        self.cli('bind', '--session', self.ids['coordinator'], '--role', 'coordinator',
                 '--task', '项目协调', '--reason', '只向一个入口提需求，其余由 Agent 安排')
        for role in ('product', 'architect', 'developer', 'tester'):
            self.cli('delegate', '--session', self.ids['coordinator'], '--target-session', self.ids[role],
                     '--role', role, '--task', self.task, '--reason', '用户授权五角色完成当前需求')
        self.product = None
        self.plan = None
        self.report = None
        self.sequence = 0

    def put(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value)

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)

    def cli(self, *args, code=0, actor=None, payload=None):
        env = {key: value for key, value in os.environ.items()
               if key not in {'CODEX_THREAD_ID', 'CLAUDE_SESSION_ID'}}
        if actor is None and '--session' in args:
            actor = args[args.index('--session') + 1]
        if actor is not None:
            env['CODEX_THREAD_ID'] = actor
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), '--root', str(self.root), *args],
                                capture_output=True, text=True, env=env,
                                input=json.dumps(payload) if payload is not None else None)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result

    def publish(self, artifact, manifest, role=None, text=None, code=0, actor=None):
        self.sequence += 1
        source = 'draft-' + str(self.sequence) + '.md'
        listing = 'manifest-' + str(self.sequence) + '.json'
        self.put(source, text or (REPORT if artifact == 'test' else DESIGN))
        self.put(listing, json.dumps(manifest, ensure_ascii=False))
        role = role or {'product': 'product', 'plan': 'architect', 'test': 'tester'}[artifact]
        result = self.cli('publish', '--session', self.ids[role], '--task', self.task,
                          '--artifact', artifact, '--source', str(self.root / source),
                          '--manifest', str(self.root / listing), '--reason', '隔离测试发布',
                          code=code, actor=actor)
        if code:
            return result
        version = result.stdout.strip()
        self.assertRegex(version, r'^[0-9a-f]{64}$')
        return version

    def confirm(self, artifact, version, role='coordinator', code=0):
        return self.cli('confirm', '--session', self.ids[role], '--task', self.task,
                        '--artifact', artifact, '--version', version, '--reason', '核对当前产物及证据', code=code)

    def setup_design(self, confirm_plan=True):
        self.product = self.publish('product', self.product_manifest)
        self.confirm('product', self.product)
        self.plan_manifest = {
            'product_version': self.product, 'assets': [self.assets + 'architecture.mmd'],
            'steps': [{'id': 'S1', 'criteria': ['A1'], 'sources': ['src/a.py']},
                      {'id': 'S2', 'criteria': ['A2'], 'sources': ['src/b.py']}]}
        self.plan = self.publish('plan', self.plan_manifest)
        if confirm_plan:
            self.confirm('plan', self.plan)
        self.put(self.task_path + '/执行记录.md', '# 执行记录\n\n## 目标与范围\n'
                 '[计划](计划.md)\nhttps://applink.feishu.cn/client/todo/detail?guid=isolated-test\n'
                 '计划版本：' + self.plan + '\n\n## 计划与进展\n已实现两个功能。\n\n'
                 '## 阻塞与决策\n无。\n\n## 验收与证据\n'
                 '- 证据 S1：2026-10-15，隔离代码检查通过。\n'
                 '- 证据 S2：2026-10-15，隔离代码检查通过。\n')
        if confirm_plan:
            self.finish_development()

    def finish_development(self):
        record = self.root / self.task_path / '执行记录.md'
        record.write_text(re.sub(r'(?m)^计划版本：[0-9a-f]+$', '计划版本：' + self.plan, record.read_text()))
        plan = self.root / self.task_path / '计划.md'
        self.put(self.task_path + '/计划.md', plan.read_text().replace('- [ ] S', '- [x] S'))

    def report_manifest(self, failed=False, issues=None):
        return {'product_version': self.product, 'plan_version': self.plan,
                'sources': ['src/a.py', 'src/b.py'],
                'cases': [{'criterion': 'A1', 'status': 'fail' if failed else 'pass', 'evidence': '断言 a.py 结果'},
                          {'criterion': 'A2', 'status': 'pass', 'evidence': '断言 b.py 结果'}],
                'issues': issues if issues is not None else
                ([{'criterion': 'A1', 'status': 'open', 'detail': 'a.py 返回错误'}] if failed else [])}

    def publish_report(self, failed=False, issues=None):
        self.report = self.publish('test', self.report_manifest(failed, issues))
        return self.report

    def rework(self, criterion='A1', role='developer', code=0):
        return self.cli('rework', '--session', self.ids['coordinator'], '--task', self.task,
                        '--version', self.report, '--criterion', criterion, '--target-role', role,
                        '--reason', '修复该项，保留原验收标准并独立复测', code=code)

    def status(self):
        return json.loads(self.cli('status', '--task', self.task).stdout)

    def hook_write(self, role, path, text, code=0):
        return self.cli('hook', code=code, actor=self.ids[role], payload={
            'hook_event_name': 'PreToolUse', 'session_id': self.ids[role],
            'cwd': str(self.root), 'tool_name': 'Write',
            'tool_input': {'file_path': path, 'content': text}})

    def test_only_coordinator_delegates_specialists_and_binding_is_fixed(self):
        for role in ('product', 'architect', 'developer', 'tester'):
            with self.subTest(role=role):
                self.cli('delegate', '--session', self.ids[role], '--target-session', 'other-' + role,
                         '--role', 'tester', '--task', self.task, '--reason', '越权分派', code=2)
        self.cli('bind', '--session', self.ids['developer'], '--role', 'tester',
                 '--task', self.task, '--reason', '同会话自测冒充独立测试', code=2)
        self.cli('delegate', '--session', self.ids['coordinator'], '--target-session', self.ids['coordinator'],
                 '--role', 'product', '--task', self.task, '--reason', '总管替代产品', code=2)

    def test_role_publication_matrix_and_actor_identity(self):
        for role in ('coordinator', 'architect', 'developer', 'tester'):
            with self.subTest(role=role):
                self.publish('product', self.product_manifest, role=role, code=2)
        self.publish('product', self.product_manifest, actor=self.ids['developer'], code=2)
        self.product = self.publish('product', self.product_manifest)
        for role in ('product', 'architect', 'developer', 'tester'):
            self.confirm('product', self.product, role=role, code=2)
        self.confirm('product', self.product)

    def test_full_flow_is_nonblocking_without_user_review_or_notices(self):
        self.setup_design()
        self.publish_report()
        self.confirm('test', self.report)
        state = self.status()
        self.assertEqual(state['current_confirmations']['test'], self.report)
        self.assertEqual({(item['artifact'], item['channel']) for item in state['pending_notices']},
                         {(artifact, channel) for artifact in ('product', 'plan', 'test')
                          for channel in ('chat', 'feishu')})

    def test_architecture_requires_confirmed_product(self):
        self.product = self.publish('product', self.product_manifest)
        manifest = {'product_version': self.product, 'assets': [self.assets + 'architecture.mmd'],
                    'steps': [{'id': 'S1', 'criteria': ['A1', 'A2'], 'sources': ['src/a.py', 'src/b.py']}]}
        self.publish('plan', manifest, text=DESIGN.replace('- [ ] S2 实现 A2\n', ''), code=2)

    def test_testing_requires_confirmed_architecture_and_independent_tester(self):
        self.setup_design(confirm_plan=False)
        self.hook_write('developer', 'src/a.py', 'answer = 3\n', code=2)
        self.publish('test', self.report_manifest(), code=2)
        self.confirm('plan', self.plan)
        self.hook_write('developer', 'src/a.py', 'answer = 3\n')
        for role in ('coordinator', 'product', 'architect', 'developer'):
            self.publish('test', self.report_manifest(), role=role, code=2)

    def test_nonowner_cannot_edit_implementation_or_published_visual_assets(self):
        self.setup_design()
        for role in ('product', 'architect', 'tester'):
            with self.subTest(role=role):
                self.hook_write(role, 'src/a.py', 'answer = 3\n', code=2)
        for role in ('architect', 'developer', 'tester'):
            with self.subTest(role=role):
                self.hook_write(role, self.assets + 'prototype.html', '<p>篡改产品</p>', code=2)
                self.hook_write(role, self.assets + 'colors.css', ':root { --text: red; }', code=2)
        self.hook_write('product', self.assets + 'architecture.mmd', 'flowchart LR\n X --> Y\n', code=2)

    def test_design_visual_assets_and_acceptance_conditions_are_required(self):
        for manifest in ({**self.product_manifest, 'assets': []},
                         {**self.product_manifest, 'criteria': []},
                         {**self.product_manifest, 'assets': [self.assets + 'missing.html']}):
            with self.subTest(manifest=manifest):
                self.publish('product', manifest, code=2)
        self.setup_design()
        self.publish('plan', {**self.plan_manifest, 'assets': []}, code=2)

    def test_html_transitive_dependency_change_invalidates_confirmation(self):
        self.setup_design()
        self.put(self.assets + 'colors.css', ':root { --text: red; }')
        self.confirm('product', self.product, code=2)
        self.publish('test', self.report_manifest(), code=2)
        new_product = self.publish('product', self.product_manifest)
        self.assertNotEqual(new_product, self.product)

    def test_html_srcset_dependency_change_invalidates_confirmation(self):
        self.put(self.assets + 'prototype.html', '<img srcset="icon.svg 1x, icon-2x.svg 2x" alt="修改前后">')
        self.put(self.assets + 'icon.svg', '<svg xmlns="http://www.w3.org/2000/svg"><title>原版</title></svg>')
        self.put(self.assets + 'icon-2x.svg', '<svg xmlns="http://www.w3.org/2000/svg"><title>原版</title></svg>')
        self.product = self.publish('product', self.product_manifest)
        self.confirm('product', self.product)
        self.put(self.assets + 'icon-2x.svg', '<svg xmlns="http://www.w3.org/2000/svg"><title>修改版</title></svg>')
        self.confirm('product', self.product, code=2)

    def test_asset_paths_cannot_escape_the_project(self):
        outside = self.root.parent / (self.root.name + '-outside.html')
        outside.write_text('<p>outside</p>')
        self.addCleanup(outside.unlink)
        self.publish('product', {**self.product_manifest, 'assets': [str(outside)]}, code=2)
        (self.root / (self.assets + 'escape.html')).symlink_to(outside)
        self.publish('product', {**self.product_manifest, 'assets': [self.assets + 'escape.html']}, code=2)

    def test_source_change_invalidates_existing_test_result(self):
        self.setup_design()
        self.publish_report()
        self.put('src/a.py', 'answer = 3\n')
        self.confirm('test', self.report, code=2)
        latest = self.publish_report()
        self.confirm('test', latest)

    def test_plan_change_invalidates_existing_test_result(self):
        self.setup_design()
        self.publish_report()
        revised = DESIGN.replace('不增加外部依赖', '保留现有依赖')
        self.publish('plan', self.plan_manifest, text=revised, code=2)
        self.plan = self.publish('plan', self.plan_manifest, text=revised.replace('- [ ] S', '- [x] S'))
        self.confirm('test', self.report, code=2)
        self.publish('test', self.report_manifest(), code=2)
        self.confirm('plan', self.plan)
        self.finish_development()
        self.publish_report()
        self.confirm('test', self.report)

    def test_test_manifest_cannot_omit_sources_or_criteria_or_evidence(self):
        self.setup_design()
        original = self.report_manifest()
        variants = [{**original, 'sources': ['src/a.py']},
                    {**original, 'cases': original['cases'][:1]},
                    {**original, 'cases': [original['cases'][0], {**original['cases'][1], 'evidence': ''}]}]
        for manifest in variants:
            with self.subTest(manifest=manifest):
                self.publish('test', manifest, code=2)

    def test_final_acceptance_rejects_failed_blocked_or_unresolved_cases(self):
        self.setup_design()
        for status in ('fail', 'blocked'):
            manifest = self.report_manifest()
            manifest['cases'][0]['status'] = status
            manifest['issues'] = [{'criterion': 'A1', 'status': 'open', 'detail': '未通过或环境阻塞'}]
            report = self.publish('test', manifest)
            self.confirm('test', report, code=2)
        report = self.publish('test', self.report_manifest(issues=[
            {'criterion': 'A1', 'status': 'open', 'detail': '断言通过，但原问题尚未解决'}]))
        self.confirm('test', report, code=2)

    def test_final_acceptance_requires_record_completed_steps_and_step_evidence(self):
        self.setup_design()
        self.publish_report()
        record = self.root / self.task_path / '执行记录.md'
        original_record = record.read_text()
        plan = self.root / self.task_path / '计划.md'
        original_plan = plan.read_text()
        record.unlink()
        self.confirm('test', self.report, code=2)
        record.write_text(original_record)
        plan.write_text(original_plan.replace('- [x] S1', '- [ ] S1'))
        self.confirm('test', self.report, code=2)
        plan.write_text(original_plan)
        for invalid in (
                original_record.replace(self.plan, '0' * 64),
                original_record.replace('[计划](计划.md)', '没有计划链接'),
                original_record.replace('## 阻塞与决策', '## 其他'),
                re.sub(r'(?m)^- 证据 S1：.*\n', '', original_record)):
            with self.subTest(invalid=invalid):
                record.write_text(invalid)
                self.confirm('test', self.report, code=2)
        record.write_text(original_record)
        self.confirm('test', self.report)

    def test_failed_report_can_publish_before_development_is_complete(self):
        self.setup_design()
        plan = self.root / self.task_path / '计划.md'
        plan.write_text(plan.read_text().replace('- [x] S1', '- [ ] S1'))
        self.publish_report(failed=True)
        self.assertEqual(self.status()['rework']['A1']['rounds'], 0)
        self.confirm('test', self.report, code=2)

    def test_status_withdraws_invalid_final_confirmation_but_keeps_history(self):
        self.setup_design()
        self.publish_report()
        self.confirm('test', self.report)
        record = self.root / self.task_path / '执行记录.md'
        original_record = record.read_text()
        plan = self.root / self.task_path / '计划.md'
        original_plan = plan.read_text()
        record.unlink()
        state = self.status()
        self.assertNotIn('test', state['current_confirmations'])
        self.assertEqual(state['confirmed']['test'], self.report)
        record.write_text(re.sub(r'(?m)^- 证据 S1：.*\n', '', original_record))
        self.assertNotIn('test', self.status()['current_confirmations'])
        record.write_text(original_record)
        plan.write_text(original_plan.replace('- [x] S1', '- [ ] S1'))
        self.assertNotIn('test', self.status()['current_confirmations'])
        plan.write_text(original_plan)
        self.assertEqual(self.status()['current_confirmations']['test'], self.report)

    def test_initial_failure_and_duplicate_publish_do_not_consume_rework_round(self):
        self.setup_design()
        self.publish_report(failed=True)
        original = self.status()
        self.assertEqual(original['rework']['A1']['rounds'], 0)
        self.publish_report(failed=True)
        self.assertEqual(self.status(), original)
        self.rework()
        self.assertEqual(self.status()['rework']['A1']['rounds'], 0)
        self.report = self.publish('test', self.report_manifest(failed=True), text=REPORT + '\n已独立执行第一次复测。\n')
        self.assertEqual(self.status()['rework']['A1']['rounds'], 1)
        after_retest = self.status()
        self.publish('test', self.report_manifest(failed=True), text=REPORT + '\n已独立执行第一次复测。\n')
        self.assertEqual(self.status(), after_retest)

    def test_three_failed_rework_rounds_pause_only_affected_steps(self):
        self.setup_design()
        self.publish_report(failed=True)
        for turn in range(3):
            self.rework(role=('developer', 'tester', 'architect')[turn])
            self.put('src/a.py', 'answer = ' + str(turn + 10) + '\n')
            if turn == 2:
                self.plan = self.publish('plan', self.plan_manifest,
                                         text=DESIGN.replace('- [ ] S', '- [x] S') + '\n第三轮架构修订。\n')
                self.confirm('plan', self.plan)
                self.finish_development()
            self.publish_report(failed=True)
            self.assertEqual(self.status()['rework']['A1']['rounds'], turn + 1)
        self.rework(code=2)
        state = self.status()
        self.assertEqual(state['blocked_criteria'], ['A1'])
        self.assertEqual(state['blocked_steps'], ['S1'])
        self.hook_write('developer', 'src/a.py', 'answer = 42\n', code=2)
        self.hook_write('developer', 'src/b.py', 'answer = 42\n')
        self.confirm('test', self.report, code=2)
        self.cli('resume', '--session', self.ids['developer'], '--task', self.task,
                 '--criterion', 'A1', '--extra-rounds', '1', '--reason', '越权恢复', code=2)
        self.cli('resume', '--session', self.ids['coordinator'], '--task', self.task,
                 '--criterion', 'A1', '--extra-rounds', '1', '--reason', '用户决定再执行一轮')
        self.rework()
        self.publish_report(issues=[{'criterion': 'A1', 'status': 'resolved', 'detail': '独立复测原失败项已通过'}])
        self.confirm('test', self.report)
        self.assertEqual(self.status()['blocked_steps'], [])

    def test_product_text_revision_keeps_identity_rounds_and_requires_reconfirmation(self):
        self.setup_design()
        self.publish_report(failed=True)
        self.rework(role='product')
        revised = {**self.product_manifest, 'criteria': [
            {'id': 'A1', 'text': '经授权修正预期结果，仍验证相同功能'}, self.product_manifest['criteria'][1]]}
        self.product = self.publish('product', revised, text=DESIGN + '\n修正原产品标准。\n')
        self.assertEqual(self.status()['rework']['A1']['rounds'], 0)
        self.assertNotIn('product', self.status()['current_confirmations'])
        self.assertNotIn('plan', self.status()['current_confirmations'])
        self.publish('test', self.report_manifest(failed=True), code=2)
        self.confirm('product', self.product)
        self.hook_write('architect', self.assets + 'architecture-draft.md', DESIGN)
        self.hook_write('architect', self.assets + 'architecture.mmd', 'flowchart LR\n A[修订前] --> B[修订后]\n')
        self.hook_write('developer', 'src/a.py', 'answer = 42\n', code=2)
        self.plan_manifest['product_version'] = self.product
        self.plan = self.publish('plan', self.plan_manifest, text=DESIGN.replace('- [ ] S', '- [x] S'))
        self.confirm('plan', self.plan)
        self.publish_report(failed=True)
        self.assertEqual(self.status()['rework']['A1']['rounds'], 1)

    def test_green_report_cannot_bypass_resume_after_three_failed_rounds(self):
        self.setup_design()
        self.publish_report(failed=True)
        for turn in range(3):
            self.rework()
            self.put('src/a.py', 'answer = ' + str(turn + 10) + '\n')
            self.publish_report(failed=True)
        before = self.status()
        self.publish('test', self.report_manifest(issues=[
            {'criterion': 'A1', 'status': 'resolved', 'detail': '无用户恢复依据的额外复测'}]), code=2)
        self.assertEqual(self.status(), before)
        self.assertEqual(before['blocked_steps'], ['S1'])
        self.confirm('test', self.report, code=2)

    def test_state_file_loss_recovers_receipts_and_does_not_downgrade_role_rules(self):
        self.setup_design()
        self.publish_report(failed=True)
        expected = self.status()
        state_file = self.root / '.git/agent-coops/tasks' / (hashlib.sha256(self.task.encode()).hexdigest() + '.json')
        state_file.unlink()
        self.assertEqual(self.status(), expected)
        self.publish('plan', self.plan_manifest, role='developer', code=2)
        self.publish('product', {**self.product_manifest, 'criteria': self.product_manifest['criteria'][1:]}, code=2)

    def test_unresolved_criterion_cannot_be_renamed_or_deleted(self):
        self.setup_design()
        self.publish_report(failed=True)
        for criteria in ([{'id': 'A9', 'text': '返回正确结果'}, self.product_manifest['criteria'][1]],
                         self.product_manifest['criteria'][1:]):
            with self.subTest(criteria=criteria):
                self.publish('product', {**self.product_manifest, 'criteria': criteria}, code=2)

    def test_open_issue_cannot_disappear_when_tests_turn_green(self):
        self.setup_design()
        self.publish_report(failed=True)
        self.rework()
        report = self.publish_report()
        self.confirm('test', report, code=2)
        self.publish_report(issues=[{'criterion': 'A1', 'status': 'resolved', 'detail': '修复结果已有独立复测证据'}])
        self.confirm('test', self.report)

    def test_notification_failure_keeps_acceptance_and_success_is_idempotent(self):
        self.setup_design()
        self.publish_report()
        self.confirm('test', self.report)
        base = ('notice', '--session', self.ids['coordinator'], '--task', self.task,
                '--artifact', 'test', '--version', self.report)
        self.cli(*base, '--channel', 'feishu', '--status', 'failed', '--error', '网络不可用')
        self.confirm('test', self.report)
        self.assertEqual(self.status()['current_confirmations']['test'], self.report)
        for channel in ('chat', 'feishu'):
            self.cli(*base, '--channel', channel, '--status', 'sent', '--receipt', channel + '-message-1')
            original = self.status()
            self.cli(*base, '--channel', channel, '--status', 'sent', '--receipt', channel + '-message-2')
            self.assertEqual(self.status(), original)
        state = json.dumps(self.status(), ensure_ascii=False)
        self.assertIn('chat-message-1', state)
        self.assertIn('feishu-message-1', state)
        self.assertNotIn('message-2', state)
        self.assertIn('网络不可用', state)

    def test_notification_requires_outcome_receipt_and_correct_version(self):
        self.setup_design()
        base = ('notice', '--session', self.ids['coordinator'], '--task', self.task,
                '--artifact', 'product', '--version', self.product, '--channel', 'feishu')
        self.cli(*base, '--status', 'sent', code=2)
        self.cli(*base, '--status', 'failed', code=2)
        changed = list(base)
        changed[changed.index('--version') + 1] = '0' * 64
        self.cli(*changed, '--status', 'sent', '--receipt', 'message-1', code=2)


if __name__ == '__main__':
    unittest.main()
