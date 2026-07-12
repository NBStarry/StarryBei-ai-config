#!/usr/bin/env bash
# Install configs only for AI coding tools already available on this machine.
# Existing files are backed up first. Skills are installed from their declared
# external marketplaces instead of copied from this repository.
#
# Usage: bash install.sh [--skip-skill-plugins]
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$HOME/.ai-config-backup-$(date +%Y%m%d-%H%M%S)"
SKIP_SKILL_PLUGINS=0
HAS_CLAUDE=0
HAS_CODEX=0

case "${1:-}" in
  "") ;;
  --skip-skill-plugins) SKIP_SKILL_PLUGINS=1 ;;
  *) echo "Usage: $0 [--skip-skill-plugins]" >&2; exit 2 ;;
esac

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

command -v claude >/dev/null 2>&1 && HAS_CLAUDE=1
command -v codex >/dev/null 2>&1 && HAS_CODEX=1

if [ "$HAS_CLAUDE" -eq 0 ] && [ "$HAS_CODEX" -eq 0 ]; then
  echo "No supported installed tools detected; nothing to install."
  exit 0
fi

# ── Claude Code ───────────────────────────────────────────────────────────
# settings.local.json is gitignored and may contain the real production backend
# token. If it exists, use it as the local runtime settings source; otherwise
# fall back to the shareable public settings.json. The old settings.glm.json
# name remains as a legacy fallback so existing machines do not break.
if [ "$HAS_CLAUDE" -eq 1 ]; then
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
else
  echo "SKIP     Claude Code config (claude is not installed)"
fi

# Custom prompts are deprecated upstream, but they are still Codex's documented
# local slash-menu adapter. Keep prompt files tiny and make skills the truth.
if [ "$HAS_CODEX" -eq 1 ]; then
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
else
  echo "SKIP     Codex config (codex is not installed)"
fi

# ── External skill plugins ────────────────────────────────────────────────
if [ "$SKIP_SKILL_PLUGINS" -eq 1 ]; then
  echo "SKIP     external skill plugins"
else
  echo
  echo "Installing external skill plugins from config/skill-plugins.json"
  bash "$REPO_DIR/scripts/install-skill-plugins.sh"
fi

# ── done ────────────────────────────────────────────────────────────────────
echo
echo "Done."
[ -d "$BACKUP_DIR" ] && echo "Backup of replaced files: $BACKUP_DIR"
echo "Next:"
[ "$HAS_CLAUDE" -eq 1 ] && echo "  - Restart your Claude Code session to pick up settings/plugins."
[ "$HAS_CODEX" -eq 1 ] && echo "  - Restart Codex or start a new Codex chat to pick up linked prompts."
echo "  - External skills are managed by config/skill-plugins.json."
echo
echo "WARNING: gitignored real config files (credentials) may live in the working tree."
echo "         Do NOT run 'git clean -x' in this repo or they will be deleted."
