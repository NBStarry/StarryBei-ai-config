#!/usr/bin/env python3
"""项目入口：只通过已安装宿主 loader 校验并调用固定规范。"""
import importlib.util
import os
from pathlib import Path
import sys


def main():
    sessions = [host for host, key in (('codex', 'CODEX_THREAD_ID'), ('hermes', 'HERMES_SESSION_ID'))
                if os.environ.get(key)]
    homes = [host for host in ('codex', 'hermes') if os.environ.get(host.upper() + '_HOME')]
    if len(sessions) > 1 or not sessions and len(homes) > 1:
        raise ValueError('WORKFLOW_HOST：宿主会话或安装目录冲突')
    host = (sessions or homes or ['codex'])[0]
    home = Path(os.environ.get(host.upper() + '_HOME') or Path.home() / ('.' + host)).expanduser()
    if host == 'codex':
        loader_path = home / 'hooks/workflow-hook.py'
    else:
        plugin = home / 'plugins/starrybei-workflow/__init__.py'
        if not plugin.is_file():
            raise ValueError('WORKFLOW_INSTALL：缺少已安装的 Team Hermes 插件')
        loader_path = plugin.resolve().parents[1] / 'codex/workflow-hook.py'
    if not loader_path.is_file():
        raise ValueError('WORKFLOW_INSTALL：缺少已安装的 Team loader')
    spec = importlib.util.spec_from_file_location('installed_team_loader', loader_path)
    loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader)
    root = Path(__file__).resolve().parents[1]
    return loader.run_cli(root, sys.argv[1:], home / 'workflow-sources.json')


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ImportError) as exc:
        print('WORKFLOW_RUNNER：' + str(exc), file=sys.stderr)
        sys.exit(2)
