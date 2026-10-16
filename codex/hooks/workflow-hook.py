#!/usr/bin/env python3
"""Codex 全局入口：按仓库调用已固定的规范，不执行项目自带代码。"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]


def project_root(cwd):
    result = subprocess.run(['git', '-C', str(cwd), 'rev-parse', '--show-toplevel'],
                            capture_output=True, text=True)
    if result.returncode == 0:
        return Path(result.stdout.strip()).resolve()
    for directory in [cwd, *cwd.parents]:
        if (directory / 'agent-coops/project.json').is_file():
            return directory
    return cwd


def run(event):
    phase = event.get('hook_event_name')
    if phase not in {'SessionStart', 'PreToolUse', 'PostToolUse', 'Stop'}:
        return 0
    cwd = Path(event.get('cwd') or Path.cwd()).resolve()
    root = project_root(cwd)
    config_path = root / 'agent-coops/project.json'
    context = 'Codex 本机原则：读取全局 AGENTS.md、项目规则、状态和当前任务。只检查本次文件；区分检查、运行与用户验收。'
    if not config_path.exists():
        if phase == 'SessionStart':
            print(json.dumps({'hookSpecificOutput': {'hookEventName': phase,
                  'additionalContext': context + ' 本项目未接入共用门禁；遵循已有项目 hook，不自动迁移。'}}, ensure_ascii=False))
        return 0
    config = json.loads(config_path.read_text())
    version = config['workflow_version']
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('WORKFLOW_VERSION：非法版本')
    script = REPO / 'workflow' / ('v' + version) / 'workflow.py'
    configured = (root / config['workflow_source'] / 'workflow.py').resolve()
    if configured != script.resolve() or script.is_symlink():
        raise ValueError('WORKFLOW_SOURCE：仅支持本配置仓的固定规范程序')
    if hashlib.sha256(script.read_bytes()).hexdigest() != config['workflow_sha256']:
        raise ValueError('WORKFLOW_PIN：程序摘要不匹配')
    # shortcut: arbitrary shell/MCP writes still require the project's candidate-commit gate.
    result = subprocess.run([sys.executable, '-B', str(script), '--root', str(root), 'hook'],
                            input=json.dumps(event), capture_output=True, text=True)
    if phase == 'SessionStart' and result.returncode == 0:
        print(json.dumps({'hookSpecificOutput': {'hookEventName': phase,
              'additionalContext': context + ' ' + result.stdout.strip()}}, ensure_ascii=False))
    else:
        print(result.stdout, end='')
    print(result.stderr, end='', file=sys.stderr)
    return result.returncode


if __name__ == '__main__':
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            raise ValueError('HOOK_INPUT：事件必须为对象')
        sys.exit(run(event))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('CODEX_WORKFLOW：' + str(exc), file=sys.stderr)
        sys.exit(2)
