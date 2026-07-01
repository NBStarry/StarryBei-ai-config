# StarryBei-ai-config

> NBStarry 的 AI 编码工具配置仓库，用来统一管理 Claude Code、Codex CLI、自建 skills、安装脚本、Dashboard 和知识库。

## 这是什么

这个仓库采用 dotfiles 式管理方式：可公开的配置文件放在仓库里，通过 `install.sh` / `install.ps1` 链接到本机工具目录；包含密钥、内网地址或硬件凭证的文件只提交 `.example` 模板，真实文件留在本地并由 `.gitignore` 保护。

它主要解决三件事：

- 新机器快速恢复 Claude Code / Codex CLI 的工作环境
- 让自建 skills、hooks、commands、agents 有统一版本管理
- 把配置、验证记录和知识 playbook 沉淀成可搜索、可审查的公开资料

## 快速开始

### macOS / Linux

```bash
git clone https://github.com/NBStarry/StarryBei-ai-config.git
cd StarryBei-ai-config
bash install.sh
```

`install.sh` 会备份已有目标文件，然后创建 symlink，并从 `.example` 模板播种本地敏感文件。已有真实文件不会被覆盖。

状态栏脚本依赖 `jq`：

```bash
brew install jq
```

### Windows

```powershell
git clone https://github.com/NBStarry/StarryBei-ai-config.git
cd StarryBei-ai-config
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

Windows 安装器会使用：

- 文件 symlink：需要开启“开发人员模式”或使用管理员 PowerShell
- 目录 junction：不需要提权，可跨盘使用
- `claude/configs/settings.windows.json`：Windows 专用 Claude Code 配置，状态栏使用 PowerShell 版本

如果文件 symlink 创建失败，脚本会保留已有配置并提示开启开发人员模式后重跑。

## 安装后需要做的事

1. 重启 Claude Code，让 settings、statusline 和插件配置生效。
2. 按脚本提示填写本地敏感文件，例如 GLM key、内网连接信息、机器人/硬件凭证。
3. 如需 Codex CLI，复制模板并登录：

```bash
cp codex/config.toml.example ~/.codex/config.toml
codex login
```

4. 修改 hzb skills 后，刷新 Claude Code 插件缓存：

```bash
claude plugin update hzb@hzb-skills
```

> 注意：本仓库工作区里会存在被 `.gitignore` 保护的真实凭证文件。不要在这里执行 `git clean -x`，否则这些本地文件会被删除。

## 仓库结构

```text
StarryBei-ai-config/
├── install.sh                 # macOS/Linux 安装器：备份、symlink、seed 模板
├── install.ps1                # Windows 安装器：文件 symlink、目录 junction、seed 模板
├── claude/                    # Claude Code 配置与扩展
│   ├── configs/               # settings、CLAUDE.md、插件清单和 .example 模板
│   ├── skills/                # Claude Code 专用 skills
│   ├── hooks/                 # Hook 配置与示例
│   ├── agents/                # Subagent 定义与示例
│   ├── commands/              # Slash command 示例
│   └── scripts/               # statusline 脚本
├── codex/                     # Codex CLI 配置模板与说明
├── skills/hzb-skills/         # 自建 hzb skill marketplace，Claude 和 Codex 共用
├── knowledge/                 # OKF-style 知识包、系统说明和 playbook
├── scripts/                   # 仓库维护脚本，例如 Dashboard 数据生成
├── site/                      # GitHub Pages Dashboard
├── docs/                      # 设计文档、历史计划和 TODO
├── deprecated/                # 已弃用方案归档
├── CLAUDE.md                  # 本仓库内协作约定
├── VERIFY.md                  # dev -> main 验证清单
└── README.md
```

## 安装内容

### Claude Code

`install.sh` 会链接这些文件：

| 本机路径 | 仓库来源 |
| --- | --- |
| `~/.claude/settings.json` | 优先 `claude/configs/settings.local.json`（gitignored），否则 `claude/configs/settings.json` |
| `~/.claude/CLAUDE.md` | `claude/configs/CLAUDE.md` |
| `~/.claude/statusline.sh` | `claude/scripts/statusline.sh` |
| `~/.claude/hzb-skills` | `skills/hzb-skills` |

`install.ps1` 的对应行为基本相同，但公开配置使用 `claude/configs/settings.windows.json`，私有生产配置可放在 gitignored 的 `claude/configs/settings.windows.local.json`，状态栏指向 `claude/scripts/statusline.ps1`。

Claude Code 相关文档：

- [claude/configs/README.md](claude/configs/README.md)
- [claude/skills/README.md](claude/skills/README.md)
- [claude/hooks/README.md](claude/hooks/README.md)
- [claude/agents/README.md](claude/agents/README.md)
- [claude/commands/README.md](claude/commands/README.md)

### Codex CLI

Codex 的 `config.toml` 不做 symlink，因为 Codex 会在运行时自动写入本机路径、project trust 和迁移提示。仓库只提供模板：

| 文件 | 说明 |
| --- | --- |
| `codex/config.toml.example` | 可复制到 `~/.codex/config.toml` 的模板 |
| `~/.codex/auth.json` | `codex login` 生成，永不入库 |
| `~/.codex/skills/<name>` | 安装器逐个链接到 `skills/hzb-skills/plugins/hzb/skills/<name>` |

详见 [codex/README.md](codex/README.md)。

## 配置管理原则

### 可公开配置使用 symlink

仓库中的公开配置是 canonical source。安装后，在 `~/.claude` 中编辑这些文件等同于修改仓库文件，后续直接 `git diff`、`git add`、`git commit` 即可。

### 敏感配置使用 `.example` 模板

真实凭证不入库。生产环境需要真实后端 token 时，不要写入 tracked 的 `settings.json` / `settings.windows.json`，应使用 gitignored 的私有 settings 文件：

| 模板 | 本地真实文件 |
| --- | --- |
| `claude/configs/settings.glm.json.example` | `claude/configs/settings.local.json` |
| `claude/configs/settings.windows.json` | `claude/configs/settings.windows.local.json` |
| `skills/hzb-skills/plugins/hzb/commands/connect-internal*.md.example` | 同目录去掉 `.example` 后缀 |
| `skills/hzb-skills/plugins/hzb/skills/g1-robot/SKILL.md.example` | `g1-robot/SKILL.md` |
| `skills/hzb-skills/plugins/hzb/skills/wlcb-dev/SKILL.md.example` | `wlcb-dev/SKILL.md` |

## hzb-skills

`skills/hzb-skills/` 是自建 directory marketplace，使用 `hzb:` 命名空间。它同时服务 Claude Code 和 Codex CLI：

- Claude Code：通过 `~/.claude/hzb-skills` 注册为 marketplace
- Codex CLI：安装器把每个 skill 链接到 `~/.codex/skills/<name>`

当前重点 skills 包括：

- `codex-review`：调用本机 Codex CLI 做独立二次审查
- `conference-meeting-summary`：整理会议转写、录音和现场 slide 照片
- `save-memory-before-compact`：压缩上下文前保存稳定记忆
- `web-access`：统一处理联网搜索、网页抓取和浏览器交互
- `g1-robot` / `wlcb-dev`：本地运维类 skill，真实内容只保留在本机

## Dashboard

`site/` 是 GitHub Pages 单页配置看板，用来浏览 skills、hooks、configs、scripts、commands、plugins 和验证状态。

- 地址：https://nbstarry.github.io/StarryBei-ai-config/
- 数据源：`site/data.json`
- 生成命令：

```bash
bash scripts/generate-site-data.sh
```

推送到 `main` 后，GitHub Actions 会发布 Dashboard。

## Knowledge

`knowledge/` 是 OKF-style 知识包，用来存放跨工具、跨主机可复用的说明和 playbook，例如：

- Hermes Agent
- Clash Verge
- 统一代理配置
- SSH / TUI proxy 环境变量

入口见 [knowledge/index.md](knowledge/index.md)。

## 日常维护

常用检查命令：

```bash
bash -n install.sh
bash -n scripts/generate-site-data.sh
bash scripts/generate-site-data.sh
```

Git 工作流：

- `dev`：所有改动先进入开发分支
- `main`：稳定分支，只包含已验证配置
- 每个需要用户验证的改动都应同步更新 [VERIFY.md](VERIFY.md)
- 相关验证项全部勾选后再合并到 `main`

## 相关文档

- [VERIFY.md](VERIFY.md)：验证清单
- [CLAUDE.md](CLAUDE.md)：本仓库协作约定
- [scripts/README.md](scripts/README.md)：维护脚本说明
- [deprecated/README.md](deprecated/README.md)：已弃用方案说明

## License

MIT License，详见 [LICENSE](LICENSE)。
