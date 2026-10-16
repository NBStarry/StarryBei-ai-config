"""Hermes 原生适配；共用规范与项目角色仍由配置仓及项目入口管理。"""
import importlib.util
import json
import logging
from pathlib import Path
import re
import subprocess
import sys
import threading

REPO = Path(__file__).resolve().parents[2]
HOOK = REPO / 'codex/hooks/workflow-hook.py'
spec = importlib.util.spec_from_file_location('starrybei_codex_workflow', HOOK)
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
_guard = threading.Lock()
_sessions = {}


def session_state(session):
    with _guard:
        return _sessions.setdefault(session, {'lock': threading.RLock(), 'roots': set(), 'started': set()})


def workspace(task_id):
    from tools.file_tools_paths import _resolve_base_dir, _terminal_env_type_for_task
    if _terminal_env_type_for_task(task_id) != 'local':
        raise ValueError('HERMES_WORKFLOW：当前规范插件只支持本地终端后端')
    return Path(_resolve_base_dir(task_id)).resolve()


def normalize(tool_name, args, cwd, task_id):
    from tools.file_tools_paths import _resolve_path_for_task
    if tool_name == 'write_file':
        return 'Write', {'file_path': str(_resolve_path_for_task(args['path'], task_id)),
                         'content': args['content']}
    if tool_name == 'patch':
        if args.get('mode', 'replace') == 'replace':
            return 'Edit', {'file_path': str(_resolve_path_for_task(args['path'], task_id)),
                            'old_string': args['old_string'], 'new_string': args['new_string'],
                            'replace_all': args.get('replace_all', False)}
        if args.get('mode') == 'patch':
            # 将 Hermes 的任务相对路径固定为绝对路径，后续选择目标仓不会改写路径含义。
            def absolute(match):
                return '*** ' + match[1] + ' File: ' + str(_resolve_path_for_task(match[2].strip(), task_id))
            patch = re.sub(r'^\*\*\*\s*(Add|Update|Delete)\s+File:\s*(.+)$',
                           absolute, args['patch'], flags=re.M)
            def move(match):
                old = Path(_resolve_path_for_task(match[1].strip(), task_id))
                new = _resolve_path_for_task(match[2].strip(), task_id)
                if not old.is_relative_to(shared.project_root(cwd)):
                    raise ValueError('PATH_ESCAPE：移动来源不属于当前项目')
                content = old.read_text()
                # shortcut: v0.1.0 的文本补丁统一末尾换行；支持其他文本格式时须升级固定规范。
                if content and not content.endswith('\n'):
                    raise ValueError('HOOK_PATCH：v0.1.0 无法精确检查无末尾换行文件的移动，未执行')
                context = '\n'.join(' ' + line for line in content.splitlines())
                return f'*** Update File: {old}\n*** Move to: {new}\n@@\n' + context
            patch = re.sub(r'^\*\*\*\s*Move\s+File:\s*(.+?)\s*->\s*(.+)$', move, patch, flags=re.M)
            return 'apply_patch', {'patch': patch}
        raise ValueError('HERMES_WORKFLOW：未知 patch 模式')
    return 'Bash', {'command': args.get('command', ''), 'workdir': str(cwd)}


def target_paths(tool_name, args, task_id):
    from tools.file_tools_paths import _resolve_path_for_task
    paths = [args['path']] if tool_name in {'write_file', 'patch'} and args.get('path') else []
    if tool_name == 'patch' and args.get('mode') == 'patch':
        from tools.file_tools import _collect_v4a_header_paths
        found = _collect_v4a_header_paths(args.get('patch', ''))
        if not isinstance(found, str):
            paths += found[0]
    return [Path(_resolve_path_for_task(path, task_id)) for path in paths]


def invoke(phase, session, cwd, tool='', args=None):
    event = dict(hook_event_name=phase, session_id=session, cwd=str(cwd),
                 tool_name=tool, tool_input=args or {})
    result = subprocess.run([sys.executable, '-B', str(HOOK)], input=json.dumps(event),
                            capture_output=True, text=True, timeout=15)
    if result.returncode:
        raise ValueError((result.stderr or result.stdout).strip() or '规范检查失败')
    return result.stdout


def context(session_id='', task_id='', **kwargs):
    try:
        cwd = workspace(task_id or session_id or 'default')
        state = session_state(session_id)
        root = shared.project_root(cwd)
        with state['lock']:
            if root in state['started']:
                return None
            raw = invoke('SessionStart', session_id, cwd)
            state['started'].add(root)
        info = json.loads(raw)['hookSpecificOutput']['additionalContext']
        principles = (REPO / 'codex/AGENTS.md').read_text()
        return {'context': principles + '\n' + info.replace('Codex 本机原则', '开发规范')}
    except Exception as exc:
        return {'context': f'HERMES_WORKFLOW：规范加载失败；停止相关开发操作并报告：{exc}'}


def execute(tool_name, args, next_call, session_id='', task_id='', **kwargs):
    if tool_name not in {'write_file', 'patch', 'terminal'}:
        return next_call(args)
    task_id = task_id or session_id or 'default'
    try:
        cwd = workspace(task_id)
        root = shared.project_root(cwd)
        # 从未接入目录直接写入已接入项目时，仍检查目标项目。
        if not (root / 'agent-coops/project.json').exists():
            for path in target_paths(tool_name, args, task_id):
                parent = path.parent
                while not parent.exists() and parent != parent.parent:
                    parent = parent.parent
                target_root = shared.project_root(parent)
                if (target_root / 'agent-coops/project.json').exists():
                    cwd = target_root
                    root = target_root
                    break
        if not (root / 'agent-coops/project.json').exists():
            return next_call(args)
        name, data = normalize(tool_name, args, cwd, task_id)
        if not session_id:
            raise ValueError('HERMES_WORKFLOW：缺少宿主 session_id，不能识别任务角色')
        state = session_state(session_id)
        # v0.1.0 每会话只有一份 pending；整个调用串行，避免并发覆盖证据。
        with state['lock']:
            state['roots'].add(root)
            invoke('PreToolUse', session_id, cwd, name, data)
            result = next_call(args)
            try:
                invoke('PostToolUse', session_id, cwd, name, data)
            except Exception as exc:
                return json.dumps({'error': str(exc), 'tool_result': result,
                                   'note': '工具已调用；结果检查失败，不自动回退或重试。'}, ensure_ascii=False)
            return result
    except Exception as exc:
        # Hermes 中间件的未处理异常会放行；显式返回错误，不能抛出检查异常。
        return json.dumps({'error': str(exc), 'note': '规范检查未通过。'}, ensure_ascii=False)


def finish(session_id='', **kwargs):
    state = session_state(session_id)
    try:
        with state['lock']:
            for root in state['roots']:
                invoke('Stop', session_id, root)
    except Exception as exc:
        return {'action': 'continue', 'message': 'HERMES_WORKFLOW：结束检查失败：' + str(exc)}
    return None


def ended(session_id='', **kwargs):
    result = finish(session_id=session_id)
    if not result:
        with _guard:
            _sessions.pop(session_id, None)
    return result


def register(ctx):
    ctx.register_hook('pre_llm_call', context)
    ctx.register_middleware('tool_execution', execute)
    ctx.register_hook('pre_verify', finish)
    ctx.register_hook('on_session_end', ended)
    logging.getLogger(__name__).info('StarryBei workflow loaded: task-aware local tool middleware')
