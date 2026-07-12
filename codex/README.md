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

Codex 与 Claude Code 共用同一套自建 skill 源——`skills/hzb-skills/plugins/hzb/skills/`。
`install.ps1` / `install.sh` 会把 `~/.codex/skills/<name>` 逐个链接到仓库内的对应 skill，
避免两套工具各维护一份副本。

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

## 为什么 config.toml 不 symlink

Codex 运行时会自动改写 `config.toml`（追加 project trust level、记录 model
migration 与 availability 提示等）。若把它 symlink 到仓库文件，这些自动写入会
污染 git 工作区，且会把本机特定路径写进公开仓库。因此 config.toml 只提供模板，
由用户复制后本地维护。
