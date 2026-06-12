#!/usr/bin/env bash
# Install AI coding tool configs by symlinking repo files into ~/.claude and
# ~/.codex. Existing files are backed up first. Sensitive files are SEEDED from
# .example templates (never overwritten if a real file already exists).
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

# copy <src> <dest>: back up existing dest, then copy (not symlink).
# Use for files the tool rewrites in place via atomic temp+rename, which would
# otherwise replace the symlink with a plain file. See settings.json below.
copy() {
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
  cp "$src" "$dest"
  echo "copied   $dest <- $src"
}

# seed <example> <real>: create real from example ONLY if real doesn't exist.
# Never overwrites — protects local credentials filled in after first install.
seed() {
  local example="$1" real="$2"
  if [ ! -e "$example" ]; then
    echo "SKIP (missing template): $example"
    return
  fi
  if [ -e "$real" ]; then
    echo "kept     $real (already exists, not overwritten)"
    return
  fi
  mkdir -p "$(dirname "$real")"
  cp "$example" "$real"
  echo "seeded   $real <- $example   (FILL IN real values)"
}

echo "Installing AI coding tool configs from $REPO_DIR"
echo

# ── Claude Code ───────────────────────────────────────────────────────────
# settings.json / CLAUDE.md are rewritten by Claude Code at runtime (/model,
# memory writes). If that uses atomic temp+rename, a symlink gets replaced by a
# plain file and drift stops syncing. We start with symlink and VERIFY this in
# Phase 4; if it breaks, switch these two `link` calls to `copy`.
link "$REPO_DIR/claude/configs/settings.json" "$HOME/.claude/settings.json"
link "$REPO_DIR/claude/configs/CLAUDE.md"     "$HOME/.claude/CLAUDE.md"
link "$REPO_DIR/claude/scripts/statusline.sh" "$HOME/.claude/statusline.sh"

# hzb-skills marketplace: directory-level symlink. Plugin loads from
# ~/.claude/plugins/cache, so this is safe; run `claude plugin update
# hzb@hzb-skills` after editing skills to refresh the cache.
link "$REPO_DIR/claude/hzb-skills" "$HOME/.claude/hzb-skills"

# Seed sensitive real files from sanitized templates (edit afterwards).
HZB="$REPO_DIR/claude/hzb-skills/plugins/hzb"
seed "$HZB/commands/connect-internal.md.example"        "$HZB/commands/connect-internal.md"
seed "$HZB/commands/connect-internal-backup.md.example" "$HZB/commands/connect-internal-backup.md"
seed "$HZB/skills/g1-robot/SKILL.md.example"            "$HZB/skills/g1-robot/SKILL.md"
seed "$HZB/skills/wlcb-dev/SKILL.md.example"            "$HZB/skills/wlcb-dev/SKILL.md"

echo
echo "NOTE: GLM backend config is not seeded (API key not in repo)."
echo "      To use it:  cp $REPO_DIR/claude/configs/settings.glm.json.example ~/.claude/settings.glm.json"
echo "      then fill in ANTHROPIC_AUTH_TOKEN."

# ── Codex CLI ───────────────────────────────────────────────────────────────
# Codex shares the same self-authored skills as Claude Code. Symlink each into
# ~/.codex/skills (repairs the previously dangling links).
for s in codex-review conference-meeting-summary g1-robot web-access wlcb-dev save-memory-before-compact; do
  if [ -d "$HZB/skills/$s" ]; then
    link "$HZB/skills/$s" "$HOME/.codex/skills/$s"
  fi
done

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
echo "  - After editing hzb skills: claude plugin update hzb@hzb-skills"
echo
echo "WARNING: gitignored real files (credentials) live in the working tree."
echo "         Do NOT run 'git clean -x' in this repo or they will be deleted."
