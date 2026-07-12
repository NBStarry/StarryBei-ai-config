#!/usr/bin/env bash
# Install AI coding tool configs by symlinking repo files into ~/.claude and
# ~/.codex. Existing files are backed up first. hzb skills are installed
# separately from https://github.com/NBStarry/hzb-skills.
#
# Usage: bash install.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$HOME/.ai-config-backup-$(date +%Y%m%d-%H%M%S)"

# ── helpers ───────────────────────────────────────────────────────────────

# link <src> <dest>: back up existing dest, then symlink dest -> src.
# Use for shareable files that the repo owns as canonical.
link() {
  local src="$1" dest="$2"
  if [ ! -e "$src" ]; then
    echo "SKIP (missing source): $src"
    return
  fi
  mkdir -p "$(dirname "$dest")"
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    mkdir -p "$BACKUP_DIR"
    mv "$dest" "$BACKUP_DIR/"
    echo "backed up $dest -> $BACKUP_DIR/"
  fi
  ln -s "$src" "$dest"
  echo "linked   $dest -> $src"
}

echo "Installing AI coding tool configs from $REPO_DIR"
echo

# ── Claude Code ───────────────────────────────────────────────────────────
# settings.local.json is gitignored and may contain the real production backend
# token. If it exists, use it as the local runtime settings source; otherwise
# fall back to the shareable public settings.json. The old settings.glm.json
# name remains as a legacy fallback so existing machines do not break.
CLAUDE_SETTINGS_SRC="$REPO_DIR/claude/configs/settings.json"
if [ -e "$REPO_DIR/claude/configs/settings.local.json" ]; then
  CLAUDE_SETTINGS_SRC="$REPO_DIR/claude/configs/settings.local.json"
  echo "using private Claude settings: $CLAUDE_SETTINGS_SRC"
elif [ -e "$REPO_DIR/claude/configs/settings.glm.json" ]; then
  CLAUDE_SETTINGS_SRC="$REPO_DIR/claude/configs/settings.glm.json"
  echo "using legacy private Claude settings: $CLAUDE_SETTINGS_SRC"
  echo "      consider renaming it to claude/configs/settings.local.json"
fi
link "$CLAUDE_SETTINGS_SRC" "$HOME/.claude/settings.json"
link "$REPO_DIR/claude/configs/CLAUDE.md"     "$HOME/.claude/CLAUDE.md"
link "$REPO_DIR/claude/scripts/statusline.sh" "$HOME/.claude/statusline.sh"

echo
echo "NOTE: GLM backend config is not seeded (API key not in repo)."
echo "      To use it: create $REPO_DIR/claude/configs/settings.local.json from"
echo "      claude/configs/settings.glm.json.example, then fill in the real token."
echo "      This file is gitignored and will be linked as ~/.claude/settings.json."

# Custom prompts are deprecated upstream, but they are still Codex's documented
# local slash-menu adapter. Keep prompt files tiny and make skills the truth.
if [ -d "$REPO_DIR/codex/prompts" ]; then
  for prompt in "$REPO_DIR"/codex/prompts/*.md; do
    [ -e "$prompt" ] || continue
    link "$prompt" "$HOME/.codex/prompts/$(basename "$prompt")"
  done
fi

echo
if [ ! -e "$HOME/.codex/config.toml" ]; then
  echo "NOTE: no ~/.codex/config.toml found."
  echo "      cp $REPO_DIR/codex/config.toml.example ~/.codex/config.toml   # then set trusted project paths"
fi

# ── done ────────────────────────────────────────────────────────────────────
echo
echo "Done."
[ -d "$BACKUP_DIR" ] && echo "Backup of replaced files: $BACKUP_DIR"
echo "Next:"
echo "  - Restart your Claude Code session to pick up settings/plugins."
echo "  - Restart Codex or start a new Codex chat to pick up linked prompts."
echo "  - Install hzb skills separately from https://github.com/NBStarry/hzb-skills"
echo
echo "WARNING: gitignored real config files (credentials) may live in the working tree."
echo "         Do NOT run 'git clean -x' in this repo or they will be deleted."
