# Repository Guidelines

## Project Overview

This public repository manages AI coding tool configuration in a dotfiles style. It contains Claude Code and Codex configuration, shared custom skills, maintenance scripts, and a GitHub Pages dashboard. The main technologies are Bash, PowerShell, Markdown, JSON, HTML, CSS, and JavaScript; there is no application build system or conventional test suite.

新增或修订的文档使用中文正文与标题。机器可读路径、命令、API 和 JSON 键保持原样；不要翻译无关历史文档。

## 项目边界与任务入口

本仓维护基础配置、通用操作与沟通原则及 Dashboard。团队规则、workflow、宿主适配和独立安装由 [SuperBeiTeam 私有仓库](https://github.com/NBStarry/SuperBeiTeam) 维护，需要访问权限。不要在本仓继续定义团队流程或复制私有正文。公开站点不得读取 Team 私有内容。

开始工作时读取 [项目工程入口](agent-coops/README.md)和当前任务记录。需求、负责人、验收要求及完成状态以本项目飞书任务为正本；`agent-coops/tasks/<任务名>/` 保存工程记录与证据。TODO、VERIFY 保留历史正文和迁移映射，不为新任务增加第二份待办状态。

本次采用 Team 已确认设计实施边界迁移；工程入口不等于已安装新门禁。未安装时继续遵守既有项目 hook。旧 `workflow/v0.1.x`、`workflow/v0.2.0` 发行文件及旧 hook/plugin 程序只作冻结兼容，见 [冻结范围](workflow/README.md)。其他项目的版本、路径和绑定不随本次变更迁移。

## Project Structure & Module Organization

- `claude/` contains Claude Code configs, hooks, commands, agents, external-skill documentation, and statusline scripts.
- `codex/` contains Codex CLI templates, prompts, and documentation.
- Shared custom hzb skills live in the separate `NBStarry/hzb-skills` repository; do not vendor them here.
- `config/external-skill-sources.json` registers public external skill sources aggregated into the Dashboard.
- `config/skill-plugins.json` declares the Claude/Codex marketplaces and plugins installed by both repository installers.
- `scripts/` contains repository maintenance scripts, including dashboard data generation.
- `config/manifest.json` is the canonical desired-state inventory consumed by the PowerShell manager and both Dashboard modes.
- `site/` contains the public GitHub Pages dashboard.
- `docs/` contains design documents, historical plans, and TODOs.
- `deprecated/` archives retired approaches; do not extend archived implementations.
- `agent-coops/` 保存本项目工程记录与任务入口。
- `TODO.md` 与 `VERIFY.md` 保留历史记录和迁移映射。

Content directories generally use a `README.md` to explain purpose and usage, an optional `examples/` directory for templates, and production files at the directory root.

## Quick Start

仅在用户要求安装到目标机器时运行安装器。读取、审查或编辑本仓库不授权修改真实用户配置。

On Windows, use PowerShell 7:

```powershell
git clone https://github.com/NBStarry/StarryBei-ai-config.git
cd StarryBei-ai-config
git checkout dev
pwsh -File .\install.ps1
```

On macOS or Linux, use Bash and install `jq`:

```bash
git clone https://github.com/NBStarry/StarryBei-ai-config.git
cd StarryBei-ai-config
git checkout dev
bash install.sh
```

Both installers link shareable configuration into the relevant user directories and back up replaced targets first. Never commit local credentials or generated authentication files.

## Architecture

### Claude Code Configuration

`claude/configs/` stores shareable settings, global instructions, plugin recommendations, and `.example` templates. The installers link `claude/configs/CLAUDE.md` to `~/.claude/CLAUDE.md`; that file contains user-wide Claude Code rules and is separate from this repository-level `AGENTS.md`.

`claude/scripts/statusline.sh` and `claude/scripts/statusline.ps1` provide the custom Claude Code status line. Hook definitions live in `claude/hooks/`, including the Bash syntax check that guards commits containing changed shell scripts.

### Dashboard

`site/` is a single-page dashboard deployed through `.github/workflows/deploy-dashboard.yml`. It presents the configuration actually in use across this repository, registered public external skill repositories, and local-only overlays.

- `scripts/generate-site-data.sh` writes the public `site/data.json` used by GitHub Pages and CI from this repository plus sources registered in `config/external-skill-sources.json`. It must only read Git-tracked files from external repositories.
- `scripts/start-local-dashboard.ps1` launches the private loopback Dashboard. Its Node server overlays installed Claude/Codex skills, plugins, and redacted local configs in memory without changing `site/data.json`.
- `site/js/editor.js` opens GitHub-native edit/new/delete pages in the owning repository and branch; authentication stays on github.com and no GitHub token is handled by the Dashboard.
- The workflow validates pull requests and pushes to `dev` / `main`. Both branches deploy GitHub Pages: `dev` provides the pre-merge preview, and the later `main` deployment restores the verified stable version.

### Extension Formats

| Type | Location | Format |
| --- | --- | --- |
| External skills | `config/external-skill-sources.json` | Public source repositories and skill roots; never vendor snapshots here |
| Installed skill plugins | `config/skill-plugins.json` | Tool-specific marketplaces and plugin selectors |
| Agents | `claude/agents/<name>.md` | Markdown with YAML frontmatter |
| Commands | `claude/commands/<name>.md` | Markdown with YAML frontmatter |
| Hooks | `claude/hooks/<name>.json` | JSON with a `hooks` object keyed by event type |
| Configs | `claude/configs/<name>.json` | Claude Code settings files |
| Plugin recommendations | `claude/configs/recommended-plugins.json` | JSON with plugin metadata and install commands |

## Build, Test, and Development Commands

- `bash install.sh` links shareable configs and installs declared external skill plugins, backing up existing targets first.
- `pwsh -File .\install.ps1` performs the corresponding Windows installation and native plugin setup.
- `pwsh -File .\scripts\validate-repo.ps1` runs the portable Windows/CI repository checks without Bash or `jq`.
- `pwsh -File .\scripts\config.ps1 plan` shows desired-vs-actual configuration state; use `apply`, `verify`, and `rollback` for the managed migration loop.
- `pwsh -File .\scripts\start-local-dashboard.ps1` opens the complete local-only Dashboard on `127.0.0.1`; use `-NoBrowser` when running it headlessly.
- `bash scripts/generate-site-data.sh` rebuilds public/CI `site/data.json` from this repository and registered public external sources.
- `for script in install.sh scripts/*.sh claude/scripts/*.sh; do bash -n "$script" || exit; done` 逐个检查维护中的 Shell 脚本，并传播失败状态。
- `jq empty claude/configs/*.json site/data.json` validates JSON files after edits.

## Git Branching & Verification

- `dev` is the development branch. All unverified changes go there first.
- `main` is the stable branch and should contain only user-verified configuration.
- 代码或配置修改与对应工程证据放在同一候选中。
- 只有本项目飞书任务中的相关用户验收全部完成后，才把 `dev` 合并到 `main`。

## Coding Style & Naming Conventions

Prefer small, explicit configuration changes. Shell scripts should use Bash with `#!/bin/bash`, `set -euo pipefail` where practical, quoted variables, and helper functions for repeated behavior. Preserve executable permissions for scripts and add a short purpose comment when the filename is not self-explanatory.

Use 2-space indentation for JSON. Markdown files should use clear headings and short actionable sections. Use kebab-case for ordinary script, config, skill, agent, command, and documentation filenames; preserve required conventional names such as `README.md`, `AGENTS.md`, `SKILL.md`, and `VERIFY.md`.

Configuration examples must use placeholder values anywhere credentials or machine-specific secrets would otherwise appear.

## Testing Guidelines

使用 `pwsh -File .\scripts\validate-repo.ps1` 运行跨平台检查。CI 在 Ubuntu 上额外检查 Bash 语法并生成公开外部来源数据，再把变化的 `site/data.json` 同步到 `dev`。需要实际观察的 UI、工具会话、账户、链接、通知或机器集成验收记录在本项目飞书任务中；工程证据保存在任务目录。纯文档检查不运行安装器或公开数据生成。

## Commit & Pull Request Guidelines

提交标题使用简短约定格式，例如 `docs(web-access): ...` 和 `chore(configs): ...`。代码、配置及相关文档或任务证据放在同一提交。PR 描述修改及验证命令，关联相关问题；Dashboard UI 修改提供截图。相关用户验收完成前，不合并到 `main`。

## Security & Configuration Tips

Do not commit real tokens, internal credentials, machine-specific secrets, or generated auth files. Use `.example` templates and gitignored local files for sensitive data. Avoid `git clean -x` in this repository because gitignored real credential files may live in the working tree.
