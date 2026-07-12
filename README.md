# StarryBei-ai-config

> NBStarry 的 AI 编码工具配置仓库，用来统一管理 Claude Code、Codex CLI、自建 skills、安装脚本、Dashboard 和知识库。

## 这是什么

这个仓库采用 dotfiles 式管理方式：可公开的配置文件放在仓库里，通过 `install.sh` / `install.ps1` 链接到本机工具目录；包含密钥、内网地址或硬件凭证的文件只提交 `.example` 模板，真实文件留在本地并由 `.gitignore` 保护。

它主要解决三件事：

- 新机器快速恢复 Claude Code / Codex CLI 的工作环境
- 让自建 skills、hooks、commands、agents 有统一版本管理
- 把配置、验证记录和知识 playbook 沉淀成可搜索、可审查的公开资料

## 快速开始

### Windows

```powershell
git clone https://github.com/NBStarry/StarryBei-ai-config.git
cd StarryBei-ai-config
pwsh -File .\install.ps1
```

Windows 安装器会使用：

- 文件 symlink：需要开启“开发人员模式”或使用管理员 PowerShell
- 目录 junction：不需要提权，可跨盘使用
- `claude/configs/settings.windows.json`：Windows 专用 Claude Code 配置，状态栏使用 PowerShell 版本

如果文件 symlink 创建失败，脚本会保留已有配置并提示开启开发人员模式后重跑。

### macOS / Linux

```bash
git clone https://github.com/NBStarry/StarryBei-ai-config.git
cd StarryBei-ai-config
bash install.sh
```

`install.sh` 会备份已有目标文件，然后创建 symlink，并从 `.example` 模板播种本地敏感文件。已有真实文件不会被覆盖。状态栏脚本依赖 `jq`，可通过系统包管理器安装。

## 安装后需要做的事

1. 重启 Claude Code，让 settings、statusline 和插件配置生效。
2. 按脚本提示填写本地敏感文件，例如 GLM key、内网连接信息、机器人/硬件凭证。
3. 如需 Codex CLI，复制模板并登录：

```powershell
Copy-Item .\codex\config.toml.example $HOME\.codex\config.toml
codex login
```

4. hzb skills 已在独立仓库维护；需要本地开发时单独 clone 并运行它的安装器：

```powershell
git clone https://github.com/NBStarry/hzb-skills.git A:\文档\Projects\hzb-skills
pwsh -NoProfile -File A:\文档\Projects\hzb-skills\install.ps1
```

> 注意：本仓库工作区里会存在被 `.gitignore` 保护的真实凭证文件。不要在这里执行 `git clean -x`，否则这些本地文件会被删除。

## 配置状态与迁移

`config/manifest.json` 是跨工具配置的目标状态清单。Windows 上可用统一的 PowerShell 入口先检查差异，再决定是否应用：

```powershell
pwsh -File .\scripts\config.ps1 doctor
pwsh -File .\scripts\config.ps1 plan
pwsh -File .\scripts\config.ps1 apply
pwsh -File .\scripts\config.ps1 verify
pwsh -File .\scripts\config.ps1 rollback
```

- `doctor` 检查 PowerShell、Git、Node、仓库、Home 和 manifest。
- `plan` 只读展示 `installed`、`missing`、`drifted` 等状态，不修改文件。
- `apply` 先把已有目标备份到 `~/.starrybei-ai-config/backups/`，再创建 symlink、junction 或一次性 seed。
- `verify` 检查本机是否已收敛到目标状态，适合脚本和 CI 调用。
- `rollback` 回滚最近一次事务；也可用 `-Transaction <id>` 指定事务。

`install.ps1` 继续保留为兼容安装入口；新状态引擎更适合审查差异、迁移新机器和可靠回滚。`codex/config.toml` 采用 `seed`，存在时不会被覆盖，因为它包含机器路径和运行时写入内容。

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
├── config/                    # 跨工具目标状态 manifest 与 JSON Schema
├── scripts/                   # 仓库维护脚本，例如 Dashboard 数据生成
├── site/                      # GitHub Pages Dashboard
├── docs/                      # 设计文档、历史计划和 TODO
├── deprecated/                # 已弃用方案归档
├── AGENTS.md                  # 本仓库内协作约定
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
| `~/.codex/skills/<name>` | 由独立的 [`hzb-skills`](https://github.com/NBStarry/hzb-skills) 仓库安装公开及本机私有 skills |

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

## hzb-skills

[`NBStarry/hzb-skills`](https://github.com/NBStarry/hzb-skills) 是独立的跨工具 marketplace，使用 `hzb:` 命名空间。本仓库只记录推荐与启用配置，不再内嵌或安装其源码。

- Claude Code：`claude plugin marketplace add NBStarry/hzb-skills`
- Codex：`codex plugin marketplace add NBStarry/hzb-skills --ref main`
- 本地开发和私有 overlay：clone 后运行独立仓库的 `install.ps1`

当前重点 skills 包括：

- `codex-review`：调用本机 Codex CLI 做独立二次审查
- `conference-meeting-summary`：整理会议转写、录音和现场 slide 照片
- `save-memory-before-compact`：压缩上下文前保存稳定记忆
- `okf`：按 Open Knowledge Format v0.1 创建和审查可移植知识包
- `web-access`：统一处理联网搜索、网页抓取和浏览器交互

## Dashboard

`site/` 是一套前端、两个数据面的配置看板：GitHub Pages 展示仓库中可公开、可复现的内容；本地版额外展示当前机器实际安装的 Claude/Codex skills、插件和配置。

- 在线地址：https://nbstarry.github.io/StarryBei-ai-config/
- 在线数据源：`site/data.json`（repo-only，不读取本机目录）
- Inventory：在线版展示 manifest 的 desired state 及 Settings、Instructions、Skills、Prompts 等具体来源内容；本地版展示脱敏后的 desired-vs-actual 状态
- 顶栏可选择 GitHub 分支并读取该分支的 `site/data.json`；`dev` 提供 GitHub 原生编辑/新建/删除入口，其他分支只读
- GitHub Actions 会生成公开的 repo-only 数据；`dev` push 后自动同步 `site/data.json`

Dashboard 不保存 GitHub token。点击 `GitHub Edit` 会打开 `github.com` 的原生编辑页，直接复用浏览器中的 GitHub 登录态并由 GitHub 完成提交认证。静态 GitHub Pages 因无法安全保存 OAuth client secret，不在前端实现 token exchange。

PR 和 `dev` / `main` push 会自动检查 PowerShell、Shell、JavaScript、JSON、skill 清单和敏感文件排除规则。两个分支都会发布 Dashboard：`dev` 用于合并前在线验收，`main` 在验收通过后恢复稳定版本；页面仍可用顶栏查看任一分支的数据。Windows 用户不需要本地运行 Bash 或 `jq` 来生成公开数据。

本地完整 Dashboard 从仓库根目录启动：

```powershell
pwsh -File .\scripts\start-local-dashboard.ps1
```

它只监听 `127.0.0.1`，在内存中合并 repo-only 数据、Claude 已安装插件、`~/.claude` / `~/.codex` / `~/.agents` skills，以及 Claude/Codex 本地配置。认证文件不会读取，配置中的 token、secret、password、API key 等字段会脱敏；本机快照不会写入 `site/data.json` 或提交到 Git。

## 日常维护

Windows 本地自动检查：

```powershell
pwsh -File .\scripts\validate-repo.ps1
```

Git 工作流：

- `dev`：所有改动先进入开发分支
- `main`：稳定分支，只包含已验证配置
- 自动检查由 GitHub Actions 执行；只有需要人工观察的改动才更新 [VERIFY.md](VERIFY.md)
- 相关验证项全部勾选后再合并到 `main`

## 相关文档

- [VERIFY.md](VERIFY.md)：验证清单
- [AGENTS.md](AGENTS.md)：本仓库协作约定
- [scripts/README.md](scripts/README.md)：维护脚本说明
- [deprecated/README.md](deprecated/README.md)：已弃用方案说明

## License

MIT License，详见 [LICENSE](LICENSE)。
