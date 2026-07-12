# Repository Guidelines

## Project Overview

This public repository manages AI coding tool configuration in a dotfiles style. It contains Claude Code and Codex configuration, shared custom skills, maintenance scripts, reusable knowledge, and a GitHub Pages dashboard. The main technologies are Bash, PowerShell, Markdown, JSON, HTML, CSS, and JavaScript; there is no application build system or conventional test suite.

Documentation is generally written in Chinese with English section headings. Keep machine-readable paths, commands, APIs, and JSON keys in their original form.

## Project Structure & Module Organization

- `claude/` contains Claude Code configs, hooks, commands, agents, skills, and statusline scripts.
- `codex/` contains Codex CLI templates, prompts, and documentation.
- `skills/hzb-skills/` contains the shared custom hzb skill marketplace used by Claude Code and Codex.
- `scripts/` contains repository maintenance scripts, including dashboard data generation.
- `config/manifest.json` is the canonical desired-state inventory consumed by the PowerShell manager and both Dashboard modes.
- `site/` contains the public GitHub Pages dashboard.
- `knowledge/` contains reusable knowledge packages, system notes, and playbooks.
- `docs/` contains design documents, historical plans, and TODOs.
- `deprecated/` archives retired approaches; do not extend archived implementations.
- `VERIFY.md` tracks user validation before changes reach `main`.

Content directories generally use a `README.md` to explain purpose and usage, an optional `examples/` directory for templates, and production files at the directory root.

## Quick Start

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

`site/` is a single-page dashboard deployed through `.github/workflows/deploy-dashboard.yml`. It presents skills, hooks, configs, scripts, plugins, and verification status.

- `scripts/generate-site-data.sh` writes the public repository-only `site/data.json` used by GitHub Pages and CI.
- `scripts/start-local-dashboard.ps1` launches the private loopback Dashboard. Its Node server overlays installed Claude/Codex skills, plugins, and redacted local configs in memory without changing `site/data.json`.
- `site/js/editor.js` opens GitHub-native edit/new/delete pages on `dev`; authentication stays on github.com and no GitHub token is handled by the Dashboard.
- The workflow validates pull requests and pushes to `dev` / `main`. Both branches deploy GitHub Pages: `dev` provides the pre-merge preview, and the later `main` deployment restores the verified stable version.

### Extension Formats

| Type | Location | Format |
| --- | --- | --- |
| Claude skills | `claude/skills/<collection>/<name>/SKILL.md` | Markdown with YAML frontmatter |
| Shared hzb skills | `skills/hzb-skills/plugins/hzb/skills/<name>/SKILL.md` | Markdown with YAML frontmatter |
| Agents | `claude/agents/<name>.md` | Markdown with YAML frontmatter |
| Commands | `claude/commands/<name>.md` | Markdown with YAML frontmatter |
| Hooks | `claude/hooks/<name>.json` | JSON with a `hooks` object keyed by event type |
| Configs | `claude/configs/<name>.json` | Claude Code settings files |
| Plugin recommendations | `claude/configs/recommended-plugins.json` | JSON with plugin metadata and install commands |

## Build, Test, and Development Commands

- `bash install.sh` links shareable configs into `~/.claude` and `~/.codex`, backing up existing targets first.
- `pwsh -File .\install.ps1` performs the corresponding Windows installation using file symlinks and directory junctions.
- `pwsh -File .\scripts\validate-repo.ps1` runs the portable Windows/CI repository checks without Bash or `jq`.
- `pwsh -File .\scripts\config.ps1 plan` shows desired-vs-actual configuration state; use `apply`, `verify`, and `rollback` for the managed migration loop.
- `pwsh -File .\scripts\start-local-dashboard.ps1` opens the complete local-only Dashboard on `127.0.0.1`; use `-NoBrowser` when running it headlessly.
- `bash scripts/generate-site-data.sh` rebuilds public/CI `site/data.json` from repository sources only.
- `bash -n install.sh scripts/*.sh claude/scripts/*.sh` checks shell syntax for maintained scripts.
- `jq empty claude/configs/*.json site/data.json` validates JSON files after edits.

## Git Branching & Verification

- `dev` is the development branch. All unverified changes go there first.
- `main` is the stable branch and should contain only user-verified configuration.
- Keep code or configuration changes and the corresponding `VERIFY.md` entry in the same commit only when observable user validation is required.
- Merge `dev` into `main` only after all relevant verification items are marked `[x]`.

Use this format for new validation items:

```markdown
- [ ] **Change summary** (commit: pending, date: YYYY-MM-DD)
  - 验证方法：how to test
  - 预期效果：expected result
  - 实际效果：（fill after verification）
```

## Coding Style & Naming Conventions

Prefer small, explicit configuration changes. Shell scripts should use Bash with `#!/bin/bash`, `set -euo pipefail` where practical, quoted variables, and helper functions for repeated behavior. Preserve executable permissions for scripts and add a short purpose comment when the filename is not self-explanatory.

Use 2-space indentation for JSON. Markdown files should use clear headings and short actionable sections. Use kebab-case for ordinary script, config, skill, agent, command, and documentation filenames; preserve required conventional names such as `README.md`, `AGENTS.md`, `SKILL.md`, and `VERIFY.md`.

Configuration examples must use placeholder values anywhere credentials or machine-specific secrets would otherwise appear.

## Testing Guidelines

Run `pwsh -File .\scripts\validate-repo.ps1` for portable checks. CI additionally runs Bash syntax and repo-only generation on Ubuntu, then automatically syncs changed `site/data.json` on `dev`. Add or update `VERIFY.md` only for behavior that requires a person to observe a real UI, tool session, account, symlink, notification, or machine integration.

## Commit & Pull Request Guidelines

Git history uses concise conventional-style subjects such as `docs(web-access): ...` and `chore(configs): ...`. Keep code/config changes and related documentation or `VERIFY.md` updates in the same commit. PRs should describe what changed, list validation commands, link issues when relevant, and include screenshots for dashboard UI changes. Do not merge to `main` until all relevant `VERIFY.md` items are marked `[x]`.

## Security & Configuration Tips

Do not commit real tokens, internal credentials, machine-specific secrets, or generated auth files. Use `.example` templates and gitignored local files for sensitive data. Avoid `git clean -x` in this repository because gitignored real credential files may live in the working tree.
