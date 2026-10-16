#!/usr/bin/env python3
"""共用协作门禁。复用 agent-coops 的候选树检查与无歧义补丁还原方式。"""
import argparse
from contextlib import contextmanager
import tempfile
import time
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from urllib.parse import unquote, urlparse

VERSION = '0.2.0'
SECTIONS = ['目标与范围', '计划与进展', '阻塞与决策', '验收与证据']
TASKS = 'agent-coops/tasks/'
BOX = re.compile(r'(?m)^- \[([ x])\] (S\d+) (.+)$')


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def body(text):
    return BOX.sub(lambda m: '- [ ] ' + m[2] + ' ' + m[3], text)


def git(root, *args, check=True):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=check).stdout


def read(path):
    return path.read_text(errors='replace') if path.is_file() else ''


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def state_dir(root):
    value = git(root, 'rev-parse', '--absolute-git-dir', check=False).decode().strip()
    return Path(value) / 'agent-coops' if value else root / '.agent-coops-local'


def task_path(task):
    if not task or task in {'.', '..'} or any(x in task for x in '/\\\n'):
        raise ValueError('TASK_NAME：任务名必须是单层目录名称')
    return TASKS + task


def checked_path(root, value):
    root = root.resolve()
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    lexical = Path(os.path.abspath(candidate))
    if not lexical.is_relative_to(root):
        lexical = lexical.resolve()
    if not lexical.is_relative_to(root) or not candidate.resolve().is_relative_to(root):
        raise ValueError('PATH_ESCAPE：路径或符号链接越出项目')
    return lexical.relative_to(root).as_posix()


def headings(text):
    found = re.findall(r'^## (.+)$', text, re.M)
    if found != SECTIONS or len(re.findall(r'^# ', text, re.M)) != 1:
        return ['DOC_FORMAT：必须有一个标题及固定四节']
    chunks = re.split(r'^## .+$', text, flags=re.M)[1:]
    return [] if all(x.strip() for x in chunks) else ['DOC_EMPTY：章节不得为空']


def publication(root, plan):
    return state_dir(root) / 'plans' / (digest(plan) + '.json')


def plan_errors(root, path, text, record, previous=''):
    errors = headings(text)
    normalized = body(text)
    receipt = publication(root, path)
    if receipt.exists():
        published = json.loads(read(receipt))['body']
    else:
        published = body(git(root, 'show', 'HEAD:' + path, check=False).decode())
    if not published or normalized != published:
        errors.append('PLAN_UNPUBLISHED：正文必须由已绑定的规划入口发布')
    revision = digest(normalized)
    if '计划版本：' + revision not in record:
        errors.append('PLAN_VERSION：执行记录必须引用当前正文哈希')
    steps = BOX.findall(text)
    ids = [x[1] for x in steps]
    if not steps or len(set(ids)) != len(ids):
        errors.append('PLAN_STEPS：步骤必须使用唯一 S编号')
    old_steps = {x[1]: x[0] for x in BOX.findall(previous)}
    for mark, step, _ in steps:
        if mark == 'x' and not re.search(r'^- 证据 ' + re.escape(step) + r'：\S.+$', record, re.M):
            errors.append('PLAN_EVIDENCE：缺少步骤证据 ' + step)
        if old_steps.get(step) == 'x' and mark != 'x' and body(previous) == normalized:
            errors.append('PLAN_UNCHECK：执行角色不能撤销已完成步骤')
    return errors


def allowed(path, config):
    return path in config['root_files'] or any(path.startswith(p.rstrip('/') + '/') for p in config['allowed_roots'])


def links(text):
    for value in re.findall(r'\[[^\]\n]*\]\(([^)\n]+)\)', text):
        value = value.strip('<>').split('#')[0]
        if value and not urlparse(value).scheme:
            yield unquote(value)


def validate_legacy(root, changes, get, config, before=lambda p: ''):
    errors = []
    related = set()
    for path, text in changes.items():
        if not allowed(path, config):
            errors.append(path + '：PATH_DENIED：未登记的目录或根文件')
        if any(path.startswith(p.rstrip('/') + '/') for p in config.get('legacy_task_roots', [])) and not before(path):
            errors.append(path + '：TASK_LEGACY：历史任务目录不再新增文件')
        if path.startswith(TASKS):
            parts = PurePosixPath(path).parts
            if len(parts) < 4:
                errors.append(path + '：TASK_LAYOUT：缺少任务目录')
                continue
            task = '/'.join(parts[:3])
            related.add(task)
            if parts[3] not in {'计划.md', '执行记录.md', 'evidence'} or (parts[3] != 'evidence' and len(parts) != 4):
                errors.append(path + '：TASK_LAYOUT：仅允许计划、执行记录及 evidence')
            if text is None and parts[3] in {'计划.md', '执行记录.md'}:
                errors.append(path + '：TASK_DELETE：任务记录不得直接删除')
        if path == 'STATUS.md' and text is not None:
            if len(text.splitlines()) > 80:
                errors.append('STATUS_LIMIT：项目状态不得超过80行')
        # Future paths in plans are not current-file links.
        if text and path.endswith('.md') and not path.endswith('/计划.md'):
            for link in links(text):
                target = os.path.normpath(str(PurePosixPath(path).parent / link))
                if target.startswith('../'):
                    continue
                if not get(target):
                    errors.append(path + '：LINK_MISSING：' + target)
    status = get('STATUS.md')
    for task in related:
        plan = task + '/计划.md'
        record = get(task + '/执行记录.md')
        if not record:
            errors.append(task + '：TASK_RECORD：缺少执行记录')
            continue
        errors += [task + '：' + e for e in headings(record)]
        if '(计划.md)' not in record:
            errors.append(task + '：TASK_LINK：缺少计划链接')
        if not re.search(r'https://[^\s)]+(?:guid=|task/)[\w-]+', record):
            errors.append(task + '：TASK_REMOTE：缺少真实飞书任务链接')
        if task + '/执行记录.md' not in status:
            errors.append(task + '：TASK_INDEX：STATUS 未登记任务')
        errors += [plan + '：' + e for e in plan_errors(root, plan, get(plan), record, before(plan))]
        if '工程结论：已完成' in record and any(mark != 'x' for mark, _, _ in BOX.findall(get(plan))):
            errors.append(task + '：TASK_INCOMPLETE：计划仍有未完成步骤')
    return errors


def apply_hunks(current, diff):
    # Reused from embodied agent-coops: reject ambiguous replacement instead of guessing.
    lines, cursor = current.splitlines(), 0
    hunks = re.split(r'(?m)^@@(?: .*?)?\n', diff)
    if len(hunks) < 2:
        raise ValueError('HOOK_PATCH：补丁需要上下文')
    for hunk in hunks[1:]:
        block = [s for s in hunk.splitlines() if not s.startswith('***')]
        if any(not s or s[0] not in ' +-' for s in block):
            raise ValueError('HOOK_PATCH：不支持的补丁行')
        old = [s[1:] for s in block if s[0] in ' -']
        new = [s[1:] for s in block if s[0] in ' +']
        indexes = [i for i in range(cursor, len(lines) - len(old) + 1) if lines[i:i + len(old)] == old]
        if '*** End of File' in hunk:
            indexes = [i for i in indexes if i + len(old) == len(lines)]
        if len(indexes) != 1:
            raise ValueError('HOOK_PATCH：补丁上下文不唯一')
        start = indexes[0]
        lines[start:start + len(old)] = new
        cursor = start + len(new)
    return '\n'.join(lines) + ('\n' if lines else '')


def tool_changes(root, event):
    data = event.get('tool_input') or {}
    name = event.get('tool_name', '').split('.')[-1]
    cwd = Path(data.get('workdir') or event.get('cwd') or root)
    def path(raw):
        return checked_path(root, cwd / raw)
    changes = {}
    if name in {'Write', 'Edit'}:
        p = path(data['file_path'])
        text = read(root / p)
        if name == 'Write':
            changes[p] = data['content']
        else:
            old = data['old_string']
            if not old or not text.count(old) or (text.count(old) > 1 and not data.get('replace_all')):
                raise ValueError('HOOK_EDIT：替换目标缺失或不唯一')
            changes[p] = text.replace(old, data['new_string'], -1 if data.get('replace_all') else 1)
    elif name == 'apply_patch':
        patch = data.get('command') or data.get('patch') or data.get('input') or ''
        matches = list(re.finditer(r'^\*\*\* (Add|Update|Delete) File: (.+)\n([\s\S]*?)(?=^\*\*\* (?:Add|Update|Delete) File:|^\*\*\* End Patch|\Z)', patch, re.M))
        if not matches:
            raise ValueError('HOOK_PATCH：无法解析补丁')
        for match in matches:
            action, raw, diff = match.groups()
            p = path(raw)
            if action == 'Delete':
                changes[p] = None
                continue
            text = ('\n'.join(s[1:] for s in diff.splitlines() if s.startswith('+')) + '\n') if action == 'Add' else apply_hunks(read(root / p), diff)
            moved = re.search(r'^\*\*\* Move to: (.+)$', diff, re.M)
            if moved:
                changes[p] = None
                p = path(moved[1])
            changes[p] = text
    return changes


def role_for(root, session):
    file = state_dir(root) / 'roles.json'
    roles = json.loads(read(file) or '{}')
    return roles.get(session, {'role': 'executor', 'task': None})


def hook(root, config, event):
    phase = event['hook_event_name']
    session = event.get('session_id', '')
    role = role_for(root, session)
    pending = state_dir(root) / 'pending' / (digest(session) + '.json')
    audit = state_dir(root) / 'events.jsonl'
    audit.parent.mkdir(parents=True, exist_ok=True)
    with audit.open('a') as stream:
        stream.write(json.dumps({'event': phase, 'session': session, 'tool': event.get('tool_name')}) + '\n')
    if phase == 'SessionStart':
        print('统一开发规范 ' + VERSION + '；读取 STATUS.md。角色：' + role['role']
              + ('；任务：' + role['task'] if role['task'] else '（未绑定）')
              + '；用户授权单入口后，由 Agent 安排子 Agent，无需用户创建开发会话；coordinator 可 delegate 规划或执行，planner 仅可 delegate 本任务执行。保留已有绑定。')
        return []
    if phase == 'PreToolUse':
        changes = tool_changes(root, event)
        if event.get('tool_name') in {'Bash', 'exec_command', 'shell_command'}:
            # shortcut: arbitrary shell writes cannot be reconstructed; candidate checks remain mandatory.
            changes = {}
        protected = {'agent-coops/project.json', 'agent-coops/run.py', '.codex/hooks.json', '.claude/settings.json', 'agent-coops/hooks/pre-commit'}
        role_errors = role_changes(root, role, changes)
        if role_errors:
            return role_errors
        for p in changes:
            if p in protected:
                return ['POLICY_PROTECTED：通过项目接入维护流程修改规则，不能在执行任务中改写']
            if p.startswith(TASKS) and len(PurePosixPath(p).parts) >= 3 and role.get('task') != PurePosixPath(p).parts[2]:
                return ['TASK_OWNER：当前入口未绑定此任务']
            if p.endswith('/计划.md'):
                if not read(root / p) or changes[p] is None or body(changes[p]) != body(read(root / p)):
                    return ['PLAN_IMMUTABLE：计划正文只能通过规划发布入口更新']
        get = lambda p: changes[p] or '' if p in changes else read(root / p)
        errors = asset_edit_errors(root, role, changes, validate(root, changes, get, config, lambda p: read(root / p)))
        if not errors:
            write_json(pending, {'paths': list(changes), 'expected': {p: digest(t) if t is not None else None for p, t in changes.items()}})
        return errors
    if phase in {'PostToolUse', 'Stop'} and pending.exists():
        info = json.loads(read(pending))
        changes = {p: read(root / p) if (root / p).exists() else None for p in info['paths']}
        # A differing version may belong to another actor; report, never revert or claim ownership.
        errors = ['HOOK_CHANGED：写入结果不同于已检查候选 ' + p for p, text in changes.items() if (digest(text) if text is not None else None) != info['expected'][p]]
        errors += asset_edit_errors(root, role, changes, validate(root, changes, lambda p: read(root / p), config))
        if not errors:
            pending.unlink()
        return errors
    return []


def check(root, config, paths, staged=False):
    if staged:
        paths = git(root, 'diff', '--cached', '--name-only', '--no-renames', '-z').decode().split('\0')
        def get(p):
            return git(root, 'show', ':' + p, check=False).decode(errors='replace')
        before = lambda p: git(root, 'show', 'HEAD:' + p, check=False).decode(errors='replace')
        candidate_config = get('agent-coops/project.json')
        if not candidate_config:
            return ['CONFIG_INDEX：候选提交缺少 project.json']
        config = json.loads(candidate_config)
        for entry in git(root, 'ls-files', '--stage', '-z').decode().split('\0'):
            if entry and entry.startswith('120000 ') and entry.split('\t', 1)[1] in paths:
                return ['PATH_SYMLINK：候选中的符号链接须单独审查，不允许直接纳入门禁范围']
    else:
        paths = [checked_path(root, p) for p in paths]
        get = lambda p: read(root / p)
        before = lambda p: ''
    changes = {p: get(p) or None for p in paths if p}
    raw = (lambda p: git(root, 'show', ':' + p, check=False) if subprocess.run(['git', '-C', str(root), 'cat-file', '-e', ':' + p], capture_output=True).returncode == 0 else None) if staged else (lambda p: (root / p).read_bytes() if (root / p).is_file() else None)
    actor = os.environ.get('CODEX_THREAD_ID') or os.environ.get('CLAUDE_SESSION_ID')
    role_errors = role_changes(root, role_for(root, actor), changes) if actor else []
    return role_errors + validate(root, changes, get, config, before, raw)


def main_unlocked():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('check'); p.add_argument('--staged', action='store_true'); p.add_argument('paths', nargs='*')
    sub.add_parser('hook')
    p = sub.add_parser('bind'); p.add_argument('--session', required=True); p.add_argument('--role', choices=['coordinator', 'product', 'architect', 'developer', 'tester', 'planner', 'executor'], required=True); p.add_argument('--task', required=True); p.add_argument('--reason', required=True, help='用户明确指定角色和任务的原话')
    p = sub.add_parser('delegate'); p.add_argument('--session', required=True); p.add_argument('--target-session', required=True); p.add_argument('--role', choices=['product', 'architect', 'developer', 'tester', 'planner', 'executor'], required=True); p.add_argument('--task', required=True); p.add_argument('--reason', required=True, help='用户授权范围内的任务安排依据')
    p = sub.add_parser('publish'); p.add_argument('--session', required=True); p.add_argument('--task', required=True); p.add_argument('--source', type=Path, required=True); p.add_argument('--reason', required=True)
    p.add_argument('--artifact', choices=['product', 'plan', 'test'], default='plan'); p.add_argument('--manifest', type=Path)
    for command in ('confirm', 'rework', 'resume', 'notice'):
        p = sub.add_parser(command); p.add_argument('--session', required=True); p.add_argument('--task', required=True)
        if command != 'notice':
            p.add_argument('--reason', required=True)
        if command in {'confirm', 'notice'}:
            p.add_argument('--artifact', choices=['product', 'plan', 'test'], required=True)
        if command != 'resume':
            p.add_argument('--version', required=True)
        if command in {'rework', 'resume'}:
            p.add_argument('--criterion', required=True)
        if command == 'rework':
            p.add_argument('--target-role', choices=['product', 'architect', 'developer', 'tester'], required=True)
        if command == 'resume':
            p.add_argument('--extra-rounds', type=int, required=True)
        if command == 'notice':
            p.add_argument('--channel', choices=['chat', 'feishu'], required=True); p.add_argument('--status', choices=['sent', 'failed'], required=True); p.add_argument('--receipt'); p.add_argument('--error')
    p = sub.add_parser('status'); p.add_argument('--task', required=True)
    args = parser.parse_args()
    actor = os.environ.get('CODEX_THREAD_ID') or os.environ.get('CLAUDE_SESSION_ID')
    if args.command in {'bind', 'delegate', 'publish', 'confirm', 'rework', 'resume', 'notice'} and actor and args.session != actor:
        raise ValueError('ROLE_ACTOR：只能使用当前宿主会话身份')
    root = args.root.resolve()
    config = json.loads(read(root / 'agent-coops/project.json'))
    if config['workflow_version'] != VERSION:
        raise ValueError('VERSION：规范版本不匹配')
    if args.command in {'confirm', 'rework', 'resume', 'notice', 'status'}:
        return stage_command(root, args)
    if args.command in {'bind', 'delegate'}:
        task_path(args.task)
        if not args.session.strip() or not args.reason.strip():
            raise ValueError('ROLE_REASON：会话 ID 和用户角色声明不能为空')
        target = args.session
        receipt = {'session': target, 'role': args.role, 'task': args.task, 'reason': args.reason}
        if args.command == 'delegate':
            source = role_for(root, args.session)
            if source['role'] != 'coordinator' and source != {'role': 'planner', 'task': args.task}:
                raise ValueError('ROLE_DENIED：只有协调入口或本任务规划入口可以分派')
            if source['role'] == 'planner' and args.role != 'executor':
                raise ValueError('ROLE_DENIED：规划入口只能分派本任务执行入口')
            target = args.target_session
            if not target.strip() or target == args.session:
                raise ValueError('ROLE_TARGET：必须指定不同的目标宿主会话')
            receipt.update(session=target, delegated_by=args.session, delegation_role=source['role'])
        file = state_dir(root) / 'roles.json'
        roles = json.loads(read(file) or '{}')
        if target in roles and roles[target] != {'role': args.role, 'task': args.task}:
            raise ValueError('ROLE_FIXED：会话角色固定；规划与执行使用不同入口')
        if target not in roles:
            roles[target] = {'role': args.role, 'task': args.task}
            write_json(state_dir(root) / 'bindings' / (digest(target) + '.json'), receipt)
            write_json(file, roles)
            if args.role in SPECIALISTS:
                state = load_task(root, args.task)
                save_task(root, args.task, state, 'bind', {'session': target, 'role': args.role})
    elif args.command == 'publish':
        if is_modern(root, args.task) or args.artifact != 'plan' or args.manifest:
            return publish_stage(root, args, config)
        if role_for(root, args.session) != {'role': 'planner', 'task': args.task}:
            raise ValueError('ROLE_DENIED：只有绑定此任务的规划入口可以发布')
        text = args.source.read_text()
        if headings(text):
            raise ValueError('; '.join(headings(text)))
        path = task_path(args.task) + '/计划.md'
        checked_path(root, path)
        old = read(root / path)
        if old:
            archive = state_dir(root) / 'history' / (digest(old) + '.md')
            archive.parent.mkdir(parents=True, exist_ok=True); archive.write_text(old)
        write_json(publication(root, path), {'body': body(text), 'sha256': digest(body(text)), 'session': args.session, 'reason': args.reason})
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(text)
        print(digest(body(text)))
    elif args.command == 'hook':
        errors = hook(root, config, json.load(sys.stdin))
        if errors:
            print('\n'.join(errors), file=sys.stderr); return 2
    else:
        if not args.staged and not args.paths:
            parser.error('check 必须指定路径或 --staged；不隐式扫描全仓')
        errors = check(root, config, args.paths, args.staged)
        if errors:
            print('\n'.join(errors), file=sys.stderr); return 2
        print('WORKFLOW_OK')
    return 0


DESIGN_SECTIONS = ['产品设计', '架构设计', '验收设计', '实施安排']
SPECIALISTS = {'product', 'architect', 'developer', 'tester'}
ARTIFACTS = {'product': '产品设计.md', 'plan': '计划.md', 'test': 'evidence/测试验收.md'}
PUBLISHERS = {'product': 'product', 'plan': 'architect', 'test': 'tester'}


def atomic_text(path, text):
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ValueError('PATH_SYMLINK：原子写入路径不得包含符号链接')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name + '-')
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def transaction(root):
    directory = state_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    if directory.is_symlink():
        raise ValueError('PATH_SYMLINK：本地状态目录不得为符号链接')
    lock = directory / 'transaction.lock'
    deadline = time.monotonic() + 10
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise ValueError('STATE_BUSY：状态事务被占用；确认进程结束后再处理遗留锁')
            time.sleep(.02)
    try:
        os.write(fd, str(os.getpid()).encode())
        yield
    finally:
        os.close(fd)
        lock.unlink()


def task_state_path(root, task):
    task_path(task)
    return state_dir(root) / 'tasks' / (digest(task) + '.json')


def load_task(root, task):
    path = task_state_path(root, task)
    current = json.loads(read(path)) if path.exists() else None
    # History is also the durable mode marker; deleting the current state cannot downgrade a task.
    history = state_dir(root) / 'task-history' / digest(task)
    snapshots = sorted(history.glob('*.json'))
    if snapshots:
        archived = json.loads(read(snapshots[-1]))
        if current is None or archived['sequence'] > current['sequence']:
            return archived
    if current is not None:
        return current
    return {'task': task, 'mode': 'five-role', 'sequence': 0, 'artifacts': {},
            'confirmed': {}, 'notices': {}, 'rework': {}, 'events': []}


def save_task(root, task, state, action, detail):
    state['sequence'] += 1
    state['events'].append({'sequence': state['sequence'], 'action': action, **detail})
    archive = state_dir(root) / 'task-history' / digest(task) / (str(state['sequence']).zfill(12) + '.json')
    write_json(archive, state)
    write_json(task_state_path(root, task), state)


def is_modern(root, task):
    if task_state_path(root, task).exists() or (state_dir(root) / 'task-history' / digest(task)).exists():
        return True
    roles = json.loads(read(state_dir(root) / 'roles.json') or '{}')
    return any(r.get('task') == task and r.get('role') in SPECIALISTS for r in roles.values()) or (root / task_path(task) / '产品设计.md').exists()


def require_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('MANIFEST：' + label + ' 必须是非空文本')
    return value


def safe_file(root, value):
    require_text(value, 'path')
    relative = checked_path(root, value)
    if any(part in {'.git', '.agent-coops-local'} for part in PurePosixPath(relative).parts):
        raise ValueError('PATH_DENIED：不能把本地状态作为产物或代码')
    return relative


def file_hash(root, path):
    path = safe_file(root, path)
    candidate = root / path
    if candidate.exists() and not candidate.is_file():
        raise ValueError('SOURCE_FILE：必须列出文件，不接受目录 ' + path)
    return hashlib.sha256(candidate.read_bytes()).hexdigest() if candidate.is_file() else None


def design_headings(text):
    found = re.findall(r'^## (.+)$', text, re.M)
    if found != DESIGN_SECTIONS or len(re.findall(r'^# ', text, re.M)) != 1:
        return ['DOC_FORMAT：设计文档必须有一个标题及产品设计、架构设计、验收设计、实施安排四节']
    return [] if all(s.strip() for s in re.split(r'^## .+$', text, flags=re.M)[1:]) else ['DOC_EMPTY：章节不得为空']


def asset_hashes(root, assets):
    if not isinstance(assets, list) or not assets:
        raise ValueError('VISUAL_REQUIRED：至少提供一份本地可视化资产')
    result = {}
    visual = False
    queue = list(assets)
    while queue:
        path = safe_file(root, queue.pop())
        if path in result:
            continue
        suffix = Path(path).suffix.lower()
        visual |= suffix in {'.html', '.htm', '.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.mmd', '.pdf'}
        result[path] = file_hash(root, path)
        if result[path] is None:
            raise ValueError('ASSET_MISSING：' + path)
        if suffix not in {'.html', '.htm', '.svg', '.css', '.js', '.mjs'}:
            continue
        text = read(root / path)
        dependencies = re.findall(r'(?:src|href|poster|data)\s*=\s*[\'"]([^\'"]+)', text, re.I)
        for candidates in re.findall(r'srcset\s*=\s*[\'"]([^\'"]+)', text, re.I):
            dependencies += re.findall(r'(?:^|,)\s*(data:[^\s]+|[^\s,]+)(?:\s+[^,]*)?', candidates)
        dependencies += re.findall(r'url\(\s*[\'"]?([^\s)\'"]+)', text, re.I)
        dependencies += re.findall(r'(?:from\s+|import\s*(?:\(\s*)?|@import\s*)[\'"]([^\'"]+)', text)
        for value in dependencies:
            if value.startswith(('#', 'data:', 'mailto:')):
                continue
            parsed = urlparse(value)
            if parsed.scheme or parsed.netloc:
                raise ValueError('ASSET_EXTERNAL：可视化依赖必须保存在项目内 ' + value)
            dependency = unquote(parsed.path)
            if not dependency:
                continue
            queue.append(str(Path(path).parent / dependency))
    if not visual:
        raise ValueError('VISUAL_REQUIRED：assets 必须包含可视化文件')
    return result


def current_errors(root, state, artifact, raw=None, get=None, seen=None):
    seen = seen or set()
    if artifact in seen:
        return []
    seen.add(artifact)
    entry = state['artifacts'].get(artifact)
    if not entry:
        return ['STAGE_MISSING：' + artifact]
    raw = raw or (lambda p: (root / p).read_bytes() if (root / p).is_file() else None)
    get = get or (lambda p: read(root / p))
    errors = []
    actual = get(entry['path'])
    if (body(actual) if artifact == 'plan' else actual) != entry['body']:
        errors.append('ARTIFACT_CHANGED：' + artifact)
    for path, expected in {**entry.get('assets', {}), **entry.get('sources', {})}.items():
        checked_path(root, path)
        data = raw(path)
        actual_hash = hashlib.sha256(data).hexdigest() if data is not None else None
        if actual_hash != expected:
            errors.append('SNAPSHOT_CHANGED：' + path)
    for parent in ('product', 'plan'):
        key = parent + '_version'
        if key in entry['manifest']:
            previous = state['artifacts'].get(parent)
            if not previous or previous['version'] != entry['manifest'][key] or state['confirmed'].get(parent) != previous['version']:
                errors.append('VERSION_CHAIN：' + parent)
            else:
                errors += current_errors(root, state, parent, raw, get, seen)
    return errors


def require_current(root, state, artifact, confirmed=False):
    errors = current_errors(root, state, artifact)
    if confirmed and state['confirmed'].get(artifact) != state['artifacts'].get(artifact, {}).get('version'):
        errors.append('STAGE_UNCONFIRMED：' + artifact)
    if errors:
        raise ValueError('; '.join(errors))
    return state['artifacts'][artifact]


def manifest_list(manifest, key):
    value = manifest.get(key)
    if not isinstance(value, list):
        raise ValueError('MANIFEST：' + key + ' 必须是数组')
    return value


def criteria_ids(product):
    return {item['id'] for item in product['manifest']['criteria']}


def plan_sources(plan):
    return {p for step in plan['manifest']['steps'] for p in step['sources']}


def failed_criteria(entry):
    return {case['criterion'] for case in entry['manifest']['cases'] if case['status'] != 'pass'} | {
        issue['criterion'] for issue in entry['manifest']['issues'] if issue['status'] == 'open'}


def publish_stage(root, args, config):
    task_path(args.task)
    if role_for(root, args.session) != {'role': PUBLISHERS[args.artifact], 'task': args.task}:
        raise ValueError('ROLE_DENIED：只有绑定此任务的对应专业角色可以发布')
    require_text(args.reason, 'reason')
    if not args.manifest:
        raise ValueError('MANIFEST：新流程必须提供 --manifest')
    source = safe_file(root, str(args.source))
    manifest_path = safe_file(root, str(args.manifest))
    text = (root / source).read_text()
    manifest = json.loads((root / manifest_path).read_text())
    if not isinstance(manifest, dict):
        raise ValueError('MANIFEST：必须是 JSON 对象')
    errors = headings(text) if args.artifact == 'test' else design_headings(text)
    if errors:
        raise ValueError('; '.join(errors))
    state = load_task(root, args.task)
    assets, sources = {}, {}
    if args.artifact in {'product', 'plan'}:
        assets = asset_hashes(root, manifest.get('assets'))
    if args.artifact == 'product':
        criteria = manifest_list(manifest, 'criteria')
        ids = []
        for item in criteria:
            if not isinstance(item, dict) or not re.fullmatch(r'A[1-9]\d*', item.get('id', '')):
                raise ValueError('CRITERIA：验收条件必须使用唯一 A编号')
            require_text(item.get('text'), 'criteria.text')
            ids.append(item['id'])
        if not ids or len(ids) != len(set(ids)):
            raise ValueError('CRITERIA：验收条件不能为空或重复')
        old = state['artifacts'].get('product')
        if old:
            existing = {item['id']: item['text'] for item in old['manifest']['criteria']}
            updated = {item['id']: item['text'] for item in criteria}
            if not set(existing) <= set(updated):
                raise ValueError('CRITERIA_FIXED：已有条件 ID 不得删除或换号；修改条件说明须保留原编号及返工历史')
    else:
        product = require_current(root, state, 'product', True)
        if manifest.get('product_version') != product['version']:
            raise ValueError('VERSION_CHAIN：必须引用已确认产品版本')
        ids = criteria_ids(product)
        if args.artifact == 'plan':
            steps = manifest_list(manifest, 'steps')
            step_ids = []
            covered = set()
            for step in steps:
                if not isinstance(step, dict) or not re.fullmatch(r'S[1-9]\d*', step.get('id', '')):
                    raise ValueError('PLAN_STEPS：步骤必须使用唯一 S编号')
                references = manifest_list(step, 'criteria')
                if not references or not set(references) <= ids:
                    raise ValueError('CRITERIA：步骤必须引用产品验收条件')
                covered.update(references)
                step['sources'] = [safe_file(root, p) for p in manifest_list(step, 'sources')]
                if not step['sources'] or any(p.startswith(TASKS) for p in step['sources']):
                    raise ValueError('SOURCE_FILE：步骤必须声明实际实现文件')
                for p in step['sources']:
                    if not allowed(p, config):
                        raise ValueError('PATH_DENIED：' + p)
                step_ids.append(step['id'])
            body_ids = [item[1] for item in BOX.findall(text)]
            if not step_ids or len(set(step_ids)) != len(step_ids) or step_ids != body_ids or covered != ids:
                raise ValueError('PLAN_STEPS：正文和 manifest 步骤须一致并覆盖全部验收条件')
        else:
            plan = require_current(root, state, 'plan', True)
            if manifest.get('plan_version') != plan['version']:
                raise ValueError('VERSION_CHAIN：必须引用已确认计划版本')
            paths = [safe_file(root, p) for p in manifest_list(manifest, 'sources')]
            if not plan_sources(plan) <= set(paths):
                raise ValueError('SOURCES_INCOMPLETE：测试快照必须覆盖计划实现文件，删除文件仍须列出')
            if any(p.startswith(TASKS) or not allowed(p, config) for p in paths):
                raise ValueError('PATH_DENIED：测试快照只能引用登记的实现文件')
            manifest['sources'] = sorted(set(paths))
            sources = {p: file_hash(root, p) for p in manifest['sources']}
            cases = manifest_list(manifest, 'cases')
            case_ids = []
            for case in cases:
                if not isinstance(case, dict) or case.get('criterion') not in ids or case.get('status') not in {'pass', 'fail', 'blocked'}:
                    raise ValueError('TEST_CASES：测试项必须引用产品条件并使用 pass/fail/blocked')
                require_text(case.get('evidence'), 'cases.evidence')
                case_ids.append(case['criterion'])
            if len(case_ids) != len(set(case_ids)) or set(case_ids) != ids:
                raise ValueError('TEST_CASES：测试项必须逐项覆盖全部适用验收条件')
            for issue in manifest_list(manifest, 'issues'):
                if not isinstance(issue, dict) or issue.get('criterion') not in ids or issue.get('status') not in {'open', 'resolved'}:
                    raise ValueError('TEST_ISSUES：缺陷必须引用稳定验收条件并标注 open/resolved')
                require_text(issue.get('detail'), 'issues.detail')
    normalized = body(text) if args.artifact == 'plan' else text
    version = digest(json.dumps({'body': normalized, 'manifest': manifest, 'assets': assets, 'sources': sources}, ensure_ascii=False, sort_keys=True))
    old = state['artifacts'].get(args.artifact)
    if old and old['version'] == version:
        print(version)
        return 0
    path = safe_file(root, task_path(args.task) + '/' + ARTIFACTS[args.artifact])
    if args.artifact == 'plan':
        completed = {step for mark, step, _ in BOX.findall(read(root / path)) if mark == 'x'}
        new_marks = {step: mark for mark, step, _ in BOX.findall(text)}
        if any(new_marks.get(step) != 'x' for step in completed):
            raise ValueError('PLAN_UNCHECK：已完成步骤不得因返工撤销或删除')
    entry = {'version': version, 'path': path, 'body': normalized, 'manifest': manifest,
             'assets': assets, 'sources': sources, 'session': args.session, 'reason': args.reason}
    if args.artifact == 'test':
        if old:
            old_cases = {case['criterion']: case for case in old['manifest']['cases']}
            new_cases = {case['criterion']: case for case in manifest['cases']}
            for criterion in blocked_criteria(state):
                if old_cases.get(criterion) != new_cases.get(criterion):
                    raise ValueError('REWORK_BLOCKED：阻塞条件须经用户决定 resume 后复测 ' + criterion)
        failures = failed_criteria(entry)
        for criterion in ids:
            item = state['rework'].get(criterion)
            if criterion in failures and not item:
                item = {'rounds': 0, 'limit': 3, 'pending': None, 'resolved': False, 'reports': []}
                state['rework'][criterion] = item
            if item:
                if item['pending'] and version not in item['reports']:
                    item['rounds'] += 1
                    item['pending'] = None
                issue_statuses = {issue['status'] for issue in manifest['issues'] if issue['criterion'] == criterion}
                if 'open' in issue_statuses:
                    item['open_issue'] = True
                elif 'resolved' in issue_statuses:
                    item['open_issue'] = False
                item['resolved'] = criterion not in failures and not item.get('open_issue', False)
                if version not in item['reports']:
                    item['reports'].append(version)
    state['artifacts'][args.artifact] = entry
    state['confirmed'].pop(args.artifact, None)
    if args.artifact == 'product':
        state['confirmed'].pop('plan', None)
    if args.artifact in {'product', 'plan'}:
        state['confirmed'].pop('test', None)
    atomic_text(root / path, text)
    save_task(root, args.task, state, 'publish', {'artifact': args.artifact, 'version': version, 'session': args.session})
    print(version)
    return 0


def blocked_criteria(state):
    return {key for key, value in state['rework'].items() if not value['resolved'] and value['rounds'] >= value['limit']}


def blocked_steps(state):
    blocked = blocked_criteria(state)
    plan = state['artifacts'].get('plan', {})
    return [step['id'] for step in plan.get('manifest', {}).get('steps', []) if blocked.intersection(step['criteria'])]


def final_readiness(root, state):
    plan = state['artifacts'].get('plan')
    if not plan:
        return ['STAGE_MISSING：plan']
    record = read(root / task_path(state['task']) / '执行记录.md')
    errors = headings(record)
    if '(计划.md)' not in record:
        errors.append('TASK_LINK：执行记录必须链接计划')
    if '计划版本：' + plan['version'] not in record:
        errors.append('PLAN_VERSION：执行记录必须引用当前计划版本')
    steps = BOX.findall(read(root / plan['path']))
    if not steps or any(mark != 'x' for mark, _, _ in steps):
        errors.append('TASK_INCOMPLETE：最终确认前必须完成全部实施步骤')
    for _, step, _ in steps:
        if not re.search(r'^- 证据 ' + re.escape(step) + r'：\S.+$', record, re.M):
            errors.append('PLAN_EVIDENCE：缺少步骤证据 ' + step)
    return errors


def stage_command(root, args):
    state = load_task(root, args.task)
    if args.command == 'status':
        output = dict(state)
        output['blocked_criteria'] = sorted(blocked_criteria(state))
        output['blocked_steps'] = blocked_steps(state)
        output['pending_notices'] = [notice for notice in state['notices'].values() if notice['status'] != 'sent']
        output['current_confirmations'] = {name: version for name, version in state['confirmed'].items()
                                           if state['artifacts'].get(name, {}).get('version') == version and not current_errors(root, state, name)
                                           and (name != 'test' or not final_readiness(root, state))}
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    if role_for(root, args.session)['role'] != 'coordinator':
        raise ValueError('ROLE_DENIED：此命令仅允许协调入口')
    if args.command != 'notice':
        require_text(args.reason, 'reason')
    if args.command == 'confirm':
        entry = require_current(root, state, args.artifact)
        if args.version != entry['version']:
            raise ValueError('VERSION_STALE：只能确认当前产物版本')
        if args.artifact == 'test' and (failed_criteria(entry) or any(not v['resolved'] for v in state['rework'].values())):
            raise ValueError('TEST_FAILED：仍有失败、阻塞或未关闭缺陷，不能最终确认')
        if args.artifact == 'test':
            errors = final_readiness(root, state)
            if errors:
                raise ValueError('; '.join(errors))
        if state['confirmed'].get(args.artifact) == args.version:
            return 0
        state['confirmed'][args.artifact] = args.version
        for channel in ('chat', 'feishu'):
            key = args.artifact + ':' + args.version + ':' + channel
            state['notices'].setdefault(key, {'artifact': args.artifact, 'version': args.version, 'channel': channel, 'status': 'pending', 'attempts': []})
    elif args.command == 'rework':
        entry = require_current(root, state, 'test')
        if args.version != entry['version'] or (args.criterion not in failed_criteria(entry) and state['rework'].get(args.criterion, {}).get('resolved', True)):
            raise ValueError('REWORK_REPORT：必须使用当前失败报告及稳定条件')
        item = state['rework'][args.criterion]
        if args.criterion in blocked_criteria(state):
            raise ValueError('REWORK_BLOCKED：已达返工上限，等待用户决定后 resume')
        if item['pending']:
            if item['pending']['version'] == args.version:
                return 0
            raise ValueError('REWORK_PENDING：上一轮尚未复测')
        if any(event['action'] == 'rework' and event.get('version') == args.version and event.get('criterion') == args.criterion for event in state['events']):
            return 0
        item['pending'] = {'version': args.version, 'target_role': args.target_role, 'reason': args.reason}
    elif args.command == 'resume':
        if args.extra_rounds <= 0 or args.criterion not in blocked_criteria(state):
            raise ValueError('REWORK_RESUME：仅对已阻塞条件明确增加正整数轮次')
        state['rework'][args.criterion]['limit'] += args.extra_rounds
    else:
        key = args.artifact + ':' + args.version + ':' + args.channel
        if key not in state['notices']:
            raise ValueError('NOTICE_UNKNOWN：不存在已确认版本的通知')
        item = state['notices'][key]
        if item['status'] == 'sent':
            return 0
        value = args.receipt if args.status == 'sent' else args.error
        require_text(value, 'receipt' if args.status == 'sent' else 'error')
        attempt = {'status': args.status, 'receipt' if args.status == 'sent' else 'error': value}
        if item['attempts'] and item['attempts'][-1] == attempt:
            return 0
        item['status'] = args.status
        item['attempts'].append(attempt)
    detail = {k: v for k, v in vars(args).items() if k not in {'root', 'command'} and v is not None}
    save_task(root, args.task, state, args.command, detail)
    return 0


def asset_edit_errors(root, role, changes, errors):
    task = role.get('task')
    if not task or not is_modern(root, task):
        return errors
    state = load_task(root, task)
    owned = {path for stage, entry in state['artifacts'].items() if PUBLISHERS[stage] == role['role']
             for path in entry.get('assets', {}) if path in changes}
    return [error for error in errors if error not in {'SNAPSHOT_CHANGED：' + path for path in owned}
            and not (owned and error.startswith('VERSION_CHAIN：'))]


def role_changes(root, role, changes):
    task = role.get('task')
    if not task or not is_modern(root, task):
        return []
    state = load_task(root, task)
    own = task_path(task) + '/'
    errors = []
    if role['role'] == 'developer' and changes:
        try:
            require_current(root, state, 'plan', True)
        except ValueError as exc:
            errors.append(str(exc))
    for path, text in changes.items():
        for stage, published in state['artifacts'].items():
            if path in published.get('assets', {}) and role['role'] != PUBLISHERS[stage]:
                errors.append('ROLE_DENIED：只能由所属设计角色更新可视化资产 ' + path)
        if path.startswith(own):
            if path in {own + '产品设计.md', own + 'evidence/测试验收.md'}:
                errors.append('ARTIFACT_IMMUTABLE：阶段产物只能由专业角色通过 publish 发布')
            if path == own + '计划.md' and role['role'] not in {'developer', 'architect'}:
                errors.append('ROLE_DENIED：当前角色不能更改实施步骤')
            if path == own + '执行记录.md' and role['role'] != 'developer':
                errors.append('ROLE_DENIED：只有开发角色写执行记录')
        elif not path.startswith(TASKS):
            if role['role'] != 'developer':
                errors.append('ROLE_DENIED：非开发角色不能写生产实现；设计和测试资料放入任务 evidence')
            else:
                try:
                    plan = require_current(root, state, 'plan', True)
                    if path not in plan_sources(plan):
                        errors.append('SOURCE_SCOPE：实现文件未列入当前计划 ' + path)
                    for step in plan['manifest']['steps']:
                        if step['id'] in blocked_steps(state) and path in step['sources']:
                            errors.append('REWORK_BLOCKED：受影响步骤等待用户决定 ' + step['id'])
                except ValueError as exc:
                    errors.append(str(exc))
    return errors


def validate(root, changes, get, config, before=lambda p: '', raw=None):
    modern = set()
    for path in changes:
        parts = PurePosixPath(path).parts
        if path.startswith(TASKS) and len(parts) >= 3 and is_modern(root, parts[2]):
            modern.add(parts[2])
    legacy = {p: t for p, t in changes.items() if not any(p.startswith(task_path(task) + '/') for task in modern)}
    errors = validate_legacy(root, legacy, get, config, before)
    if raw is None:
        raw = lambda p: (changes[p].encode() if changes[p] is not None else None) if p in changes else ((root / p).read_bytes() if (root / p).is_file() else None)
    for task in modern:
        base = task_path(task) + '/'
        state = load_task(root, task)
        for path, text in changes.items():
            if not path.startswith(base):
                continue
            if not allowed(path, config):
                errors.append('PATH_DENIED：' + path)
            relative = path[len(base):]
            if relative not in {'产品设计.md', '计划.md', '执行记录.md'} and not relative.startswith('evidence/'):
                errors.append('TASK_LAYOUT：仅允许阶段设计、执行记录和 evidence ' + path)
            if text is None and relative in {'产品设计.md', '计划.md', '执行记录.md', 'evidence/测试验收.md'}:
                errors.append('TASK_DELETE：不得删除任务阶段产物 ' + path)
        for artifact, filename in ARTIFACTS.items():
            if get(base + filename) and artifact not in state['artifacts']:
                errors.append('ARTIFACT_UNPUBLISHED：阶段产物必须通过对应角色发布 ' + artifact)
        for artifact, entry in state['artifacts'].items():
            if entry['path'] in changes or any(path in changes for path in entry.get('assets', {})):
                errors += current_errors(root, state, artifact, raw, get)
        record = get(base + '执行记录.md')
        if record and (base + '执行记录.md' in changes or base + '计划.md' in changes):
            errors += headings(record)
            plan = state['artifacts'].get('plan')
            if not plan or '计划版本：' + plan['version'] not in record:
                errors.append('PLAN_VERSION：执行记录必须引用当前计划版本')
            if '(计划.md)' not in record:
                errors.append('TASK_LINK：执行记录必须链接计划')
        plan_text = get(base + '计划.md')
        if plan_text and base + '计划.md' in changes:
            old_steps = {step: mark for mark, step, _ in BOX.findall(before(base + '计划.md'))}
            for mark, step, _ in BOX.findall(plan_text):
                if mark == 'x' and not re.search(r'^- 证据 ' + re.escape(step) + r'：\S.+$', record, re.M):
                    errors.append('PLAN_EVIDENCE：缺少步骤证据 ' + step)
                if old_steps.get(step) == 'x' and mark != 'x':
                    errors.append('PLAN_UNCHECK：失败不能撤销已完成步骤 ' + step)
                if mark == 'x' and old_steps and old_steps.get(step) != 'x' and step in blocked_steps(state):
                    errors.append('REWORK_BLOCKED：受影响步骤等待用户决定 ' + step)
    return errors


def main():
    # Serialize CLI state changes; publication files are checked against the committed receipt after interruptions.
    probe = argparse.ArgumentParser(add_help=False)
    probe.add_argument('--root', type=Path)
    args, _ = probe.parse_known_args()
    if not args.root or '--help' in sys.argv:
        return main_unlocked()
    with transaction(args.root.resolve()):
        return main_unlocked()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        print('WORKFLOW_ERROR：' + str(exc), file=sys.stderr)
        sys.exit(2)
