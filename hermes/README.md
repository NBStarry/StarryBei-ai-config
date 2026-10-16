# Hermes 冻结适配说明

团队规则、Hermes 适配、成员配置及安装与回退由 [SuperBeiTeam 私有仓库](https://github.com/NBStarry/SuperBeiTeam) 维护，需要仓库访问权限。基础配置安装不再发现 Hermes、链接团队插件或修改 `plugins.enabled`。已有安装保持原样。

## 旧版兼容

`workflow-plugin/` 保留为既有消费者的冻结适配器，插件 ID 仍为 `starrybei-workflow`。本次不修改插件程序，也不删除旧链接。旧 `scripts/install-workflow.py --tool hermes` 及 `--rollback` 只显示迁移提示；请保留原回执和备份，按 Team 安装与回退说明处理。

旧适配器引用本仓固定版本，详见 [workflow 冻结范围](../workflow/README.md)。新接入和功能维护在 Team 进行；切换版本须有明确授权。历史部署与限制见 [原规范维护记录](../docs/plans/2026-10-13-codex-root-principles.md)，该记录不作为当前安装说明。

## 冻结版本回归

隔离检查：

```bash
python3 -B -m unittest discover -s codex/tests -v
python3 -B -m unittest discover -s workflow/v0.1.0/tests -v
```

需要目标 Hermes 源码和虚拟环境时，执行原生适配回归：

```bash
HERMES_SOURCE="$HOME/.hermes/hermes-agent" \
  ~/.hermes/hermes-agent/venv/bin/python -B hermes/tests/test_native_runtime.py -v
```

原生回归在临时 Hermes 目录建立插件 fixture，测试插件发现、上下文和工具分发，不调用基础安装器或模型。自动检查、真实宿主运行与用户验收分别记录。新安装的实际运行证据由 Team 保存。
