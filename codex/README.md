# Codex CLI 配置

本目录管理 OpenAI Codex CLI（`~/.codex/`）的可分享配置。

## 文件说明

| 文件 | 用途 | 是否纳入版本管理 |
|------|------|------------------|
| `config.toml.example` | Codex 主配置模板（模型、TUI、项目信任） | ✅ 模板入库 |
| `~/.codex/config.toml` | 实际配置 | ❌ 仅本地（Codex 会自动改写，含本机路径） |
| `~/.codex/auth.json` | OAuth token | ❌ 绝不入库（`codex login` 生成） |

## Skills

Codex 与 Claude Code 共用同一套自建 skill 源——`skills/hzb-skills/plugins/hzb/skills/`。
`install.sh` 会把 `~/.codex/skills/<name>` 逐个 symlink 指向仓库内的对应 skill，
避免两套工具各维护一份副本。

## 首次安装

```bash
# 1. 配置（模板 → 实际）
cp config.toml.example ~/.codex/config.toml   # 然后填入你的项目信任路径
codex login                                    # 生成 auth.json

# 2. skills 由仓库根目录的 install.sh 统一链接
bash ../install.sh
```

## 为什么 config.toml 不 symlink

Codex 运行时会自动改写 `config.toml`（追加 project trust level、记录 model
migration 与 availability 提示等）。若把它 symlink 到仓库文件，这些自动写入会
污染 git 工作区，且会把本机特定路径写进公开仓库。因此 config.toml 只提供模板，
由用户复制后本地维护。
