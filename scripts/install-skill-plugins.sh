#!/usr/bin/env bash
# Install the external plugins that provide the skills represented by this repo.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$REPO_ROOT/config/skill-plugins.json"
PLAN=0

case "${1:-}" in
  "") ;;
  --plan) PLAN=1 ;;
  *) echo "Usage: $0 [--plan]" >&2; exit 2 ;;
esac

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required to read config/skill-plugins.json" >&2
  exit 1
fi

marketplace_args() {
  local tool="$1" repository="$2" branch="$3"
  if [ "$tool" = "claude" ]; then
    printf 'plugin\tmarketplace\tadd\t%s\n' "$repository"
  else
    printf 'plugin\tmarketplace\tadd\t%s\t--ref\t%s\t--json\n' "$repository" "$branch"
  fi
}

plugin_args() {
  local tool="$1" selector="$2"
  if [ "$tool" = "claude" ]; then
    printf 'plugin\tinstall\t%s\t--scope\tuser\n' "$selector"
  else
    printf 'plugin\tadd\t%s\t--json\n' "$selector"
  fi
}

find_tool() {
  local tool="$1" candidate
  if command -v "$tool" >/dev/null 2>&1; then
    command -v "$tool"
    return
  fi
  for candidate in "$HOME/.local/bin/$tool" "/opt/homebrew/bin/$tool" "/usr/local/bin/$tool"; do
    if [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return
    fi
  done
  return 1
}

for tool in claude codex; do
  if [ "$PLAN" -eq 1 ]; then
    while IFS=$'\t' read -r repository branch; do
      [ -n "$repository" ] || continue
      printf '%s ' "$tool"
      marketplace_args "$tool" "$repository" "$branch" | tr '\t' ' '
    done < <(jq -r --arg tool "$tool" '.marketplaces[] | select(.tools | index($tool)) | [.repository, .branch] | @tsv' "$MANIFEST")
    while IFS=$'\t' read -r name marketplace; do
      [ -n "$name" ] || continue
      printf '%s ' "$tool"
      plugin_args "$tool" "${name}@${marketplace}" | tr '\t' ' '
    done < <(jq -r --arg tool "$tool" '.plugins[] | select(.tools | index($tool)) | [.name, .marketplace] | @tsv' "$MANIFEST")
    continue
  fi

  tool_cmd="$(find_tool "$tool" || true)"
  if [ -z "$tool_cmd" ]; then
    echo "WARN: $tool is not installed; skipping its skill plugins." >&2
    continue
  fi

  if [ "$tool" = "claude" ]; then
    marketplace_state=$("$tool_cmd" plugin marketplace list --json)
    plugin_state=""
  else
    marketplace_state=$("$tool_cmd" plugin marketplace list --json)
    plugin_state=""
  fi

  while IFS=$'\t' read -r id repository branch; do
    [ -n "$id" ] || continue
    if [ "$tool" = "claude" ]; then
      exists=$(jq -r --arg id "$id" 'any(.[]; .name == $id)' <<<"$marketplace_state")
    else
      exists=$(jq -r --arg id "$id" 'any(.marketplaces[]; .name == $id)' <<<"$marketplace_state")
    fi
    if [ "$exists" = "true" ]; then
      echo "present  $tool marketplace $id"
      continue
    fi
    echo "adding   $tool marketplace $id"
    IFS=$'\t' read -r -a args < <(marketplace_args "$tool" "$repository" "$branch")
    "$tool_cmd" "${args[@]}"
  done < <(jq -r --arg tool "$tool" '.marketplaces[] | select(.tools | index($tool)) | [.id, .repository, .branch] | @tsv' "$MANIFEST")

  if [ "$tool" = "claude" ]; then
    plugin_state=$("$tool_cmd" plugin list --json)
  else
    plugin_state=$("$tool_cmd" plugin list --json)
  fi

  while IFS=$'\t' read -r name marketplace; do
    [ -n "$name" ] || continue
    selector="${name}@${marketplace}"
    if [ "$tool" = "claude" ]; then
      exists=$(jq -r --arg id "$selector" 'any(.[]; .id == $id)' <<<"$plugin_state")
    else
      exists=$(jq -r --arg id "$selector" 'any(.installed[]; .pluginId == $id)' <<<"$plugin_state")
    fi
    if [ "$exists" = "true" ]; then
      echo "present  $tool plugin $selector"
      continue
    fi
    echo "install  $tool plugin $selector"
    IFS=$'\t' read -r -a args < <(plugin_args "$tool" "$selector")
    "$tool_cmd" "${args[@]}"
  done < <(jq -r --arg tool "$tool" '.plugins[] | select(.tools | index($tool)) | [.name, .marketplace] | @tsv' "$MANIFEST")
done
