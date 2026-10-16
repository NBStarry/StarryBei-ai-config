#!/usr/bin/env python3
"""共用协作门禁。复用 agent-coops 的候选树检查与无歧义补丁还原方式。"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from urllib.parse import unquote, urlparse

VERSION = '0.1.1'
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
    return path.read_text() if path.is_file() else ''


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temp.replace(path)


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


def validate(root, changes, get, config, before=lambda p: ''):
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
              + ('；任务：' + role['task'] if role['task'] else '（未绑定）；用户明确指定角色和任务后，由 Agent 调用 bind 登记当前会话，无需用户运行命令'))
        return []
    if phase == 'PreToolUse':
        changes = tool_changes(root, event)
        if event.get('tool_name') in {'Bash', 'exec_command', 'shell_command'}:
            # shortcut: arbitrary shell writes cannot be reconstructed; candidate checks remain mandatory.
            changes = {}
        protected = {'agent-coops/project.json', 'agent-coops/run.py', '.codex/hooks.json', '.claude/settings.json', 'agent-coops/hooks/pre-commit'}
        for p in changes:
            if p in protected:
                return ['POLICY_PROTECTED：通过项目接入维护流程修改规则，不能在执行任务中改写']
            if p.startswith(TASKS) and role.get('task') != PurePosixPath(p).parts[2]:
                return ['TASK_OWNER：当前入口未绑定此任务']
            if p.endswith('/计划.md'):
                if not read(root / p) or changes[p] is None or body(changes[p]) != body(read(root / p)):
                    return ['PLAN_IMMUTABLE：计划正文只能通过规划发布入口更新']
        get = lambda p: changes[p] or '' if p in changes else read(root / p)
        errors = validate(root, changes, get, config, lambda p: read(root / p))
        if not errors:
            write_json(pending, {'paths': list(changes), 'expected': {p: digest(t) if t is not None else None for p, t in changes.items()}})
        return errors
    if phase in {'PostToolUse', 'Stop'} and pending.exists():
        info = json.loads(read(pending))
        changes = {p: read(root / p) if (root / p).exists() else None for p in info['paths']}
        # A differing version may belong to another actor; report, never revert or claim ownership.
        errors = ['HOOK_CHANGED：写入结果不同于已检查候选 ' + p for p, text in changes.items() if (digest(text) if text is not None else None) != info['expected'][p]]
        errors += validate(root, changes, lambda p: read(root / p), config)
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
    return validate(root, changes, get, config, before)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('check'); p.add_argument('--staged', action='store_true'); p.add_argument('paths', nargs='*')
    sub.add_parser('hook')
    p = sub.add_parser('bind'); p.add_argument('--session', required=True); p.add_argument('--role', choices=['planner', 'executor'], required=True); p.add_argument('--task', required=True); p.add_argument('--reason', required=True, help='用户明确指定角色和任务的原话')
    p = sub.add_parser('publish'); p.add_argument('--session', required=True); p.add_argument('--task', required=True); p.add_argument('--source', type=Path, required=True); p.add_argument('--reason', required=True)
    args = parser.parse_args()
    actor = os.environ.get('CODEX_THREAD_ID') or os.environ.get('CLAUDE_SESSION_ID')
    if args.command in {'bind', 'publish'} and actor and args.session != actor:
        raise ValueError('ROLE_ACTOR：只能使用当前宿主会话身份')
    root = args.root.resolve()
    config = json.loads(read(root / 'agent-coops/project.json'))
    if config['workflow_version'] != VERSION:
        raise ValueError('VERSION：规范版本不匹配')
    if args.command == 'bind':
        task_path(args.task)
        if not args.session.strip() or not args.reason.strip():
            raise ValueError('ROLE_REASON：会话 ID 和用户角色声明不能为空')
        file = state_dir(root) / 'roles.json'
        roles = json.loads(read(file) or '{}')
        if args.session in roles and roles[args.session] != {'role': args.role, 'task': args.task}:
            raise ValueError('ROLE_FIXED：会话角色固定；规划与执行使用不同入口')
        if args.session not in roles:
            roles[args.session] = {'role': args.role, 'task': args.task}
            write_json(state_dir(root) / 'bindings' / (digest(args.session) + '.json'),
                       {'session': args.session, 'role': args.role, 'task': args.task, 'reason': args.reason})
            write_json(file, roles)
    elif args.command == 'publish':
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


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        print('WORKFLOW_ERROR：' + str(exc), file=sys.stderr)
        sys.exit(2)
