# StarryBei-ai-config

> NBStarry 的 AI 编码工具配置、脚本与扩展合集

## About

这是一个公开的配置仓库，统一管理日常使用的各种 AI 编码工具（Claude Code、Codex 等）的配置文件、自定义脚本、hooks、skills、agents 和 commands。

采用 dotfiles 式的 symlink 管理：可公开的配置软链进仓库版本管理，含密钥的部分拆分为 `.example` 模板（真实文件由 `.gitignore` 保护，不入库）。新机器 clone 后跑一次 `install.sh`，再填几个敏感文件即可恢复工作环境。

如果你也在用这些工具，希望这些配置能为你提供参考和灵感。

## Repository Structure

```
StarryBei-ai-config/
├── install.sh           # 统一安装器（symlink + .example 播种 + 自动备份）
├── claude/              # ── Claude Code ──
│   ├── configs/         #   settings.json / CLAUDE.md / *.example
│   ├── hzb-skills/      #   自建 skill marketplace（hzb: 命名空间）
│   ├── skills/          #   skill 定义与示例（含官方插件副本）
│   ├── hooks/           #   Hook 配置与示例
│   ├── agents/          #   Agent 定义与示例
│   ├── commands/        #   Slash command 示例
│   └── scripts/         #   statusline.sh
├── codex/               # ── Codex CLI ──
│   ├── config.toml.example
│   └── README.md
├── scripts/             # 共享脚本（generate-site-data.sh、export-memory.sh）
├── site/                # GitHub Pages Dashboard
├── docs/                # 设计文档与历史计划
├── deprecated/          # 废案归档（QQ / Telegram 通知、旧 sync-configs）
├── CLAUDE.md            # 本仓库的 Claude Code 约定
├── VERIFY.md            # dev → main 验证清单
└── README.md           # 本文件
```

## Quick Start

```bash
git clone https://github.com/NBStarry/StarryBei-ai-config.git
cd StarryBei-ai-config

# 一键安装：把可公开配置 symlink 到 ~/.claude、~/.codex，
# 并从 .example 播种敏感文件（已存在则不覆盖），原文件自动备份
bash install.sh
```

安装后按提示填入敏感配置（GLM key、机器人/内网凭证等），详见各工具子目录的 `.example` 模板。

## Claude Code

`claude/` 下管理 Claude Code 的全局配置与扩展。

### Configs

| 文件 | 说明 | 入库形式 |
|------|------|----------|
| `claude/configs/settings.json` | 全局配置（插件、statusline、model），已移除代理与密钥 | ✅ symlink 目标 |
| `claude/configs/CLAUDE.md` | 全局编码规则（装到 `~/.claude/CLAUDE.md`） | ✅ symlink 目标 |
| `claude/configs/settings.glm.json.example` | GLM 后端配置模板（key 占位） | ✅ 模板 |
| `claude/configs/settings.local.json.example` | 项目级配置示例 | ✅ 模板 |
| `claude/configs/recommended-plugins.json` | 推荐插件列表 | ✅ |

代理设置不再写进 `settings.json`，改由 shell 环境变量继承（参考 `~/.zshrc`）。

### hzb-skills（自建 skill marketplace）

`claude/hzb-skills/` 是以 `hzb:` 命名空间组织的自建 skill 合集，作为 directory 类型的 plugin marketplace 注册。`install.sh` 会把 `~/.claude/hzb-skills` 整目录 symlink 指向这里，因此改 skill 后只需 `claude plugin update hzb@hzb-skills` 刷新缓存。

含内网/硬件凭证的运维类 skill（`g1-robot`、`wlcb-dev`、`connect-internal*`）以脱敏 `.example` 入库，真实文件由 `.gitignore` 保护并由 `install.sh` 播种到本地。

### statusline.sh

自定义状态栏，显示 `◆会话名 · 路径 · 模型 · 分支 · 上下文%`：

```
◆my-session · ~/AI_Projects/…/StarryBei-ai-config · opus·1M · main · 34%
```

颜色编码上下文使用率（绿 < 50% / 黄 50-80% / 红 ≥ 80%）。依赖 `jq`。

详见 [claude/skills/README.md](claude/skills/README.md)、[claude/hooks/README.md](claude/hooks/README.md)、[claude/agents/README.md](claude/agents/README.md)、[claude/commands/README.md](claude/commands/README.md)。

## Codex CLI

`codex/` 管理 OpenAI Codex CLI 配置。Codex 与 Claude Code 共用同一套自建 skill 源（`claude/hzb-skills/`），`install.sh` 会把 `~/.codex/skills/<name>` 逐个 symlink 指向仓库内对应 skill。

`config.toml` 因 Codex 运行时会自动改写（追加 project trust 等），不做 symlink，只提供 `config.toml.example` 模板。`auth.json`（OAuth token）绝不入库。

详见 [codex/README.md](codex/README.md)。

## Dashboard (GitHub Pages)

`site/` 是部署到 GitHub Pages 的单页配置看板，展示 skills / hooks / configs / scripts / commands / plugins 与验证状态，并支持通过 GitHub API 在线编辑配置。

- 数据生成：`scripts/generate-site-data.sh` 扫描仓库目录，输出 `site/data.json`
- 部署：push 到 `main` 时由 GitHub Actions 自动构建发布
- 地址：`https://nbstarry.github.io/StarryBei-ai-config/`

## 配置同步机制

采用 **symlink + `.example` 分离** 混合模式（取代旧的 `sync-configs.sh` 双向复制）：

- **可公开配置**：`install.sh` 把它们 symlink 进 `~/.claude` / `~/.codex`，在原位编辑即等于改仓库文件，`git add/commit/push` 即同步
- **敏感内容**：拆为 `.example` 模板入库，真实文件 `.gitignore` 保护；`install.sh` 用 `seed`（仅当本地不存在时复制）从模板播种，绝不覆盖已有真实文件

> ⚠️ 因含密真实文件靠 `.gitignore` 保护而物理存在于工作区，**请勿在本仓库执行 `git clean -x`**，否则会删除这些本地凭证文件。

## Agent Teams / 团队协作

Claude Code 实验性功能，支持多 agent 协同。

```json
// ~/.claude/settings.json
{ "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }

// .claude/settings.local.json
{ "teammateMode": "in-process" }
```

| 参数 | 推荐值 | 原因 |
|------|--------|------|
| `mode` | `acceptEdits` | `default` 会导致 teammate 卡在权限审批 |
| Lead `model` | `opus` | 复杂编排需要强模型 |
| Teammate `model` | `sonnet` | 平衡能力与成本，禁用 haiku |
| `teammateMode` | `in-process` | 比 tmux 分 pane 切换更方便 |

踩坑：`mode: "default"` 会卡死（权限提示 lead 收不到）；在 prompt 中明确「不要自行 commit」；teammate 可能崩溃需检查进程存活。

## Git 工作流

- `main` — 稳定分支，仅含用户验证过的配置
- `dev` — 开发分支，所有改动先进这里
- 每个 `dev` commit 必须在 `VERIFY.md` 同步添加验证条目
- 所有相关 `VERIFY.md` 条目勾选 `[x]` 后才合并到 `main`

## Environment

| 项目 | 详情 |
|------|------|
| 操作系统 | macOS (Darwin) |
| 工具 | Claude Code、Codex CLI |
| 默认模型 | Claude Opus |

## License

MIT License - 详见 [LICENSE](LICENSE) 文件。

---

*Made with Claude Code by NBStarry*
