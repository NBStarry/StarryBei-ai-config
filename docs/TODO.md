# TODO / 待办

> 跨机器、跨会话的长期待办。完成后移除条目并在 commit 说明。

## Skills 全量纳管到仓库

- **现状**：仓库目前只纳管了**自建** skill（`skills/hzb-skills/`，`hzb` 命名空间）。`claude/configs/settings.json` 与 `settings.windows.json` 的 `enabledPlugins` 虽引用了官方与第三方插件（`github`、`superpowers`、`skill-creator`、`claude-mem` 等），但这些**官方 / 第三方 skill 的完整安装清单尚未在仓库中记录**，新机器无法据此恢复全部 skill 环境。
- **待办**：
  - 盘点各机器（macOS / Windows）`~/.claude/plugins/` 下实际安装的全部 marketplace / plugin / skill。
  - 在仓库中统一记录（扩充 `claude/configs/recommended-plugins.json`，或新增安装清单文档），并让 `install.sh` / `install.ps1` 能据此自动注册 marketplace + 启用插件。
  - 目标：新机器跑一次安装脚本即可恢复**完整** skill 环境，而不仅是自建 skill。
- **来源**：Windows 适配时发现安装脚本仅处理了自建 skill（hzb），官方/第三方仅靠 `enabledPlugins` 声明、缺少集中清单。
