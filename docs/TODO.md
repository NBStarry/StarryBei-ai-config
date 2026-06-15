# TODO / 待办

> 跨机器、跨会话的长期待办。完成后移除条目并在 commit 说明。

## Skills 全量纳管到仓库

- **现状（2026-06-15 更新）**：已盘点 `longxiabei` Mac 的 `~/.claude/plugins/`，把 marketplace / plugin / skill 记入 `claude/configs/recommended-plugins.json`（6 个 marketplace、21 个插件，含各插件携带的 skill 名）。新增发现并补录：`telegram` 及全部官方插件。
- **已移除**：`pua` / `pua-skills`（tanweai/pua）——用户不喜欢，已从仓库清单、`longxiabei` Mac 全部删除；`hanzebei` Mac 离线，上线后需补删（见下）。
- **已完成**：
  - [x] 盘点 macOS（longxiabei）已装 marketplace / plugin / skill。
  - [x] `recommended-plugins.json` 改为多 marketplace 结构（`marketplaces[]` + `plugins[]`，每个插件带 `marketplace` 与 `skills`）。
- **仍待办**：
  - [ ] 盘点 **hanzebei** Mac（当前离线）——它可能有 longxiabei 之外的源/插件，需上线后补录、与本清单合并；**并删除其上的 pua / pua-skills**（若已安装）。
  - [ ] 让 `install.sh` / `install.ps1` 读取 `recommended-plugins.json`，自动 `claude plugin marketplace add` 各 github 源（目前 github 源靠 `settings.json` 的 `extraKnownMarketplaces` 在加载时注册，但 `pua-skills` 等尚未写入各机 settings）。
  - [ ] 决定各机器（Windows / 各 Mac）实际要 **启用** 哪些插件（`enabledPlugins` 是每机偏好，不必全开）；如需在 Windows 启用 pua/telegram 等，再写入 `settings.windows.json`。
- **来源**：Windows 适配时发现安装脚本仅处理了自建 skill（hzb），官方/第三方仅靠 `enabledPlugins` 声明、缺少集中清单。
