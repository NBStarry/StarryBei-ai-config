# Codex CLI 配置

本目录管理 OpenAI Codex CLI（`~/.codex/`）的可分享配置。

## 文件说明

| 文件 | 用途 | 是否纳入版本管理 |
|------|------|------------------|
| `config.toml.example` | Codex 主配置模板（模型、TUI、项目信任） | ✅ 模板入库 |
| `prompts/*.md` | Codex 本地 slash-menu prompt 适配器 | ✅ 模板入库 |
| `~/.codex/config.toml` | 实际配置 | ❌ 仅本地（Codex 会自动改写，含本机路径） |
| `~/.codex/prompts/*.md` | `install.ps1` / `install.sh` 链接出的本地 prompt | ❌ 仅本地入口 |
| `~/.codex/auth.json` | OAuth token | ❌ 绝不入库（`codex login` 生成） |

## Skills

Codex 与 Claude Code 共用的自建 skills 已迁移到独立仓库
[`NBStarry/hzb-skills`](https://github.com/NBStarry/hzb-skills)。本仓库的安装器管理
Codex 配置模板、prompt adapter、基础操作与沟通原则和 `config/skill-plugins.json` 中声明的公开 plugin。
本机私有 skill 链接由各自的安装流程负责。

## Slash prompt 适配器

Codex 不会把 `.agents/skills/<name>` 自动注册成 `/<name>` slash command。
官方仍支持但已标注 deprecated 的本地 Custom Prompts 可以把
`~/.codex/prompts/*.md` 暴露到 slash 菜单，调用形式是
`/prompts:<name>`。

本仓只把这类文件当作薄适配器使用：`codex/prompts/checkpoint.md`
会被安装器链接到 `~/.codex/prompts/checkpoint.md`，提供
`/prompts:checkpoint` 入口；真正的 checkpoint 规则仍以当前项目里的
`checkpoint` skill、`scripts/checkpoint.sh` 和 `AGENTS.md` 为准。
新增或修改 prompt 后，需要重启 Codex 或新开 Codex chat 才会加载。

## 首次安装

```powershell
# 从仓库根目录运行，统一链接 Claude/Codex skills 和 prompts
pwsh -File .\install.ps1

# 若 config.toml 尚不存在，复制模板后填写项目信任路径
Copy-Item .\codex\config.toml.example $HOME\.codex\config.toml
codex login
```

macOS/Linux 使用仓库根目录的 `bash install.sh`。

## VS Code 终端标题

`config.toml.example` 的 `tui.terminal_title` 会让 Codex 通过 OSC 标题序列输出
运行状态和会话名。VS Code 还需要把终端 Tab 标题来源切换为 `${sequence}`；仓库
中的 [vscode/settings.json](../vscode/settings.json) 提供了可合并到用户设置的最小片段。

不要用该片段覆盖现有的 VS Code `settings.json`。合并设置并重启 Codex 后，空闲时
Tab 显示会话名，运行时显示类似 `⠋ session-name` 的活动状态。

## 为什么 config.toml 不 symlink

Codex 运行时会自动改写 `config.toml`（追加 project trust level、记录 model
migration 与 availability 提示等）。若把它 symlink 到仓库文件，这些自动写入会
污染 git 工作区，且会把本机特定路径写进公开仓库。因此 config.toml 只提供模板，
由用户复制后本地维护。

## 基础原则与团队兼容入口

`AGENTS.md` 是 Codex 基础原则正本。两个基础安装器将它链接到 `~/.codex/AGENTS.md`，`config/manifest.json` 保留该受管项。项目规则继续决定目录、任务格式和验证命令。

团队规则、Codex 团队 hook、安装与回退由 [SuperBeiTeam 私有仓库](https://github.com/NBStarry/SuperBeiTeam) 维护，需要访问权限。基础安装器不再合并 `hooks.json`，也不删除已有团队 hook。旧 `--workflow-only`、`-WorkflowOnly` 和 `scripts/install-workflow.py` 只提示 Team 入口。

`hooks/workflow-hook.py` 保留为冻结兼容文件。已使用它的项目继续使用原路径和固定版本，迁移须明确授权。旧程序字节不在本次边界迁移中修改。冻结范围见 [workflow 兼容说明](../workflow/README.md)。

本仓回归命令为 `python3 -B -m unittest discover -s codex/tests -v`。测试使用临时配置目录，不改变真实宿主配置。工程证据见 [边界迁移工程入口](../agent-coops/tasks/team-boundary-migration/README.md)。历史部署事实保留在 [原规范维护记录](../docs/plans/2026-10-13-codex-root-principles.md)，该记录不作为当前安装说明。
