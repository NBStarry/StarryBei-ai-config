#!/usr/bin/env python3
"""项目入口：固定共用门禁版本与摘要，不复制业务规则。"""
import hashlib
import json
from pathlib import Path
import runpy
import sys

root = Path(__file__).resolve().parents[1]
config = json.loads((root / 'agent-coops/project.json').read_text())
script = (root / config['workflow_source'] / 'workflow.py').resolve()
if hashlib.sha256(script.read_bytes()).hexdigest() != config['workflow_sha256']:
    sys.exit('WORKFLOW_PIN：共用程序摘要改变；检查版本后由接入维护流程更新')
sys.dont_write_bytecode = True
sys.argv = [str(script), '--root', str(root), *sys.argv[1:]]
runpy.run_path(str(script), run_name='__main__')
