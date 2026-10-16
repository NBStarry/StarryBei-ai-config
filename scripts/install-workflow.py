#!/usr/bin/env python3
"""仅安装开发规范；保留宿主配置并记录可校验的回退快照。"""
import argparse
import base64
from datetime import datetime
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
PLUGIN = 'starrybei-workflow'


def snapshot(path):
    if path.is_symlink():
        return {'link': os.readlink(path)}
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError(f'目标不是文件或链接：{path}')
    return {'data': base64.b64encode(path.read_bytes()).decode(),
            'mode': stat.S_IMODE(path.stat().st_mode)}


def restore(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if value is None:
        path.unlink(missing_ok=True)
        return
    fd, name = tempfile.mkstemp(prefix='.workflow-', dir=path.parent)
    os.close(fd)
    temp = Path(name)
    try:
        if 'link' in value:
            temp.unlink()
            temp.symlink_to(value['link'], target_is_directory=Path(value['link']).is_dir())
        else:
            temp.write_bytes(base64.b64decode(value['data']))
            temp.chmod(value['mode'])
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def text_state(text, mode=0o600):
    return {'data': base64.b64encode(text.encode()).decode(), 'mode': mode}


def desired(tool, home):
    if tool == 'codex':
        config = home / 'hooks.json'
        data = json.loads(config.read_text()) if config.exists() else {}
        if not isinstance(data, dict):
            raise ValueError('hooks.json 顶层必须是对象')
        hooks = data.setdefault('hooks', {})
        if not isinstance(hooks, dict):
            raise ValueError('hooks 必须是对象')
        command = 'python3 -B "$HOME/.codex/hooks/workflow-hook.py"'
        if os.name == 'nt' or home != Path.home() / '.codex':
            parts = [sys.executable, '-B', str(home / 'hooks/workflow-hook.py')]
            command = subprocess.list2cmdline(parts) if os.name == 'nt' else shlex.join(parts)
        for event in ('SessionStart', 'PreToolUse', 'PostToolUse', 'Stop'):
            groups = hooks.setdefault(event, [])
            if not isinstance(groups, list):
                raise ValueError(f'{event} 必须是数组')
            found = [(g, h) for g in groups for h in g.get('hooks', [])
                     if 'workflow-hook.py' in h.get('command', '')]
            wanted = dict(type='command', command=command, timeout=10,
                          statusMessage='Codex 规范检查')
            if found:
                if (len(found) != 1 or found[0][1] != wanted
                        or found[0][0].get('matcher') not in (None, '', '*')):
                    raise ValueError(f'{event} 已有不同的规范 hook，请先核对，避免重复执行')
            else:
                groups.append({'hooks': [wanted]})
        return {
            home / 'AGENTS.md': {'link': str(REPO / 'codex/AGENTS.md')},
            home / 'hooks/workflow-hook.py': {'link': str(REPO / 'codex/hooks/workflow-hook.py')},
            config: text_state(json.dumps(data, ensure_ascii=False, indent=2) + '\n'),
        }
    # Hermes 已依赖 PyYAML；使用其虚拟环境运行本脚本，不另装依赖。
    import yaml
    config = home / 'config.yaml'
    data = yaml.safe_load(config.read_text()) if config.exists() else {}
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError('config.yaml 顶层必须是对象')
    plugins = data.setdefault('plugins', {})
    enabled = plugins.setdefault('enabled', [])
    if not isinstance(enabled, list):
        raise ValueError('plugins.enabled 必须是数组')
    if PLUGIN in plugins.get('disabled', []):
        raise ValueError('规范插件被显式禁用；请先核对停用原因')
    if PLUGIN not in enabled:
        enabled.append(PLUGIN)
    output = {home / 'plugins' / PLUGIN: {'link': str(REPO / 'hermes/workflow-plugin')}}
    if not config.exists() or yaml.safe_load(config.read_text()) != data:
        output[config] = text_state(yaml.safe_dump(data, allow_unicode=True, sort_keys=False))
    return output


def install(tool, home):
    changes = []
    for path, after in desired(tool, home).items():
        if 'link' in after and not Path(after['link']).exists():
            raise ValueError(f'安装源不存在：{after["link"]}')
        before = snapshot(path)
        if before != after:
            changes.append(dict(path=str(path), before=before, after=after))
    if not changes:
        print('UNCHANGED：规范已安装')
        return None
    backup_root = home / 'backups'
    backup_root.mkdir(parents=True, exist_ok=True)
    backup = Path(tempfile.mkdtemp(prefix='workflow-' + datetime.now().strftime('%Y%m%d-%H%M%S-'), dir=backup_root))
    receipt = backup / 'receipt.json'
    receipt.write_text(json.dumps({'tool': tool, 'changes': changes}, ensure_ascii=False, indent=2))
    receipt.chmod(0o600)
    applied = []
    try:
        for change in changes:
            path = Path(change['path'])
            if snapshot(path) != change['before']:
                raise ValueError(f'安装期间目标被修改：{path}')
            restore(path, change['after'])
            applied.append(change)
    except Exception:
        for change in reversed(applied):
            if snapshot(Path(change['path'])) == change['after']:
                restore(Path(change['path']), change['before'])
        raise
    print('INSTALLED：' + str(receipt))
    if tool == 'codex':
        print('在 Codex /hooks 审阅并信任新增定义，然后新开会话验证。')
    else:
        print('重新加载 Hermes 进程后验证插件；安装不自动重启网关。')
    return receipt


def rollback(receipt):
    changes = json.loads(receipt.read_text())['changes']
    for change in changes:
        if snapshot(Path(change['path'])) != change['after']:
            raise ValueError(f'安装后目标已变化，拒绝覆盖：{change["path"]}')
    for change in reversed(changes):
        restore(Path(change['path']), change['before'])
    print('ROLLED_BACK：' + str(receipt))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool', choices=['codex', 'hermes'])
    parser.add_argument('--home', type=Path, help='宿主配置目录，如 ~/.codex 或 ~/.hermes')
    parser.add_argument('--rollback', type=Path, help='恢复本脚本打印的 receipt.json')
    args = parser.parse_args()
    if args.rollback:
        if args.tool or args.home:
            parser.error('--rollback 不与安装参数同时使用')
        rollback(args.rollback.expanduser().resolve())
    else:
        if not args.tool:
            parser.error('安装需要 --tool')
        home = (args.home or Path.home() / ('.' + args.tool)).expanduser().absolute()
        install(args.tool, home)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError, ImportError) as exc:
        print('WORKFLOW_INSTALL：' + str(exc), file=sys.stderr)
        sys.exit(1)
