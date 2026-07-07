# Repository Guidelines

## Project Structure & Module Organization

This repository manages AI coding tool configuration in a dotfiles style. `claude/` contains Claude Code configs, hooks, commands, agents, skills, and statusline scripts. `codex/` contains Codex CLI templates and documentation. Shared custom skills live in `skills/hzb-skills/`. Maintenance scripts are in `scripts/`, public dashboard assets are in `site/`, reusable knowledge and playbooks are in `knowledge/`, and older approaches are archived in `deprecated/`. Use `VERIFY.md` to track user validation before changes reach `main`.

## Build, Test, and Development Commands

- `bash install.sh` links shareable configs into `~/.claude` and `~/.codex`, backing up existing targets first.
- `bash scripts/generate-site-data.sh` rebuilds `site/data.json` for the GitHub Pages dashboard.
- `bash -n install.sh scripts/*.sh claude/scripts/*.sh` checks shell syntax for maintained scripts.
- `jq empty claude/configs/*.json site/data.json` validates JSON files after edits.

## Coding Style & Naming Conventions

Prefer small, explicit configuration changes. Shell scripts should use Bash with `set -euo pipefail` where practical, quoted variables, and helper functions for repeated behavior. Markdown files should use clear headings and short actionable sections. Skill directories use kebab-case names, for example `skills/hzb-skills/plugins/hzb/skills/web-access/`.

## Testing Guidelines

Test the actual runtime path for script or installer changes, not just syntax. For shell scripts, run `bash -n` and then invoke the script with representative arguments or inputs. Regenerate `site/data.json` after changing skills, hooks, configs, scripts, commands, or dashboard metadata. Add or update a pending item in `VERIFY.md` for changes that require user validation.

## Commit & Pull Request Guidelines

Git history uses concise conventional-style subjects such as `docs(web-access): ...` and `chore(configs): ...`. Keep code/config changes and related documentation or `VERIFY.md` updates in the same commit. PRs should describe what changed, list validation commands, link issues when relevant, and include screenshots for dashboard UI changes. Do not merge to `main` until all relevant `VERIFY.md` items are marked `[x]`.

## Security & Configuration Tips

Do not commit real tokens, internal credentials, machine-specific secrets, or generated auth files. Use `.example` templates and gitignored local files for sensitive data. Avoid `git clean -x` in this repository because gitignored real credential files may live in the working tree.