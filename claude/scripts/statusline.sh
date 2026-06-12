#!/bin/bash

# Read JSON input from stdin
input=$(cat)

current_dir=$(pwd)

# ---- Session name ----
# Use Claude Code's own session_name (from /rename or auto-generated)
# Fall back to basename of cwd if empty
session_name=$(echo "$input" | jq -r '.session_name // empty')
[ -z "$session_name" ] && session_name=$(basename "$current_dir")

# Short path: replace $HOME with ~, keep first 2 + last 2 segments
short_path="${current_dir/#$HOME/~}"
IFS='/' read -ra parts <<< "$short_path"
n=${#parts[@]}
if [ $n -gt 5 ]; then
    short_path="${parts[0]}/${parts[1]}/…/${parts[$((n-2))]}/${parts[$((n-1))]}"
fi

# ---- Model (shorten "X.Y (1M context)" → "X.Y·1M") ----
model_name=$(echo "$input" | jq -r '.model.display_name // empty')
model_name=$(echo "$model_name" | sed -E 's/ ?\(1M context\)/·1M/; s/ ?\(with 1M context\)/·1M/')

# ---- Git branch ----
git_branch=""
if git rev-parse --git-dir > /dev/null 2>&1; then
    branch=$(git --no-optional-locks branch --show-current 2>/dev/null)
    [ -n "$branch" ] && git_branch="$branch"
fi

# ---- Context % ----
ctx_info=""
remaining_pct=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')
if [ -n "$remaining_pct" ] && [ "$remaining_pct" != "null" ]; then
    used_pct=$(awk "BEGIN {printf \"%.0f\", 100 - $remaining_pct}")
    if [ "$used_pct" -lt 50 ]; then ctx_color="\033[01;32m"
    elif [ "$used_pct" -lt 80 ]; then ctx_color="\033[01;33m"
    else ctx_color="\033[01;31m"
    fi
    ctx_info="${ctx_color}${used_pct}%\033[00m"
fi

# ---- Output: ◆project · path · model · branch · ctx% ----
out="\033[01;35m◆${session_name}\033[00m"
[ -n "$short_path" ] && out="${out} · \033[01;34m${short_path}\033[00m"
[ -n "$model_name" ] && out="${out} · \033[01;36m${model_name}\033[00m"
[ -n "$git_branch" ] && out="${out} · \033[01;33m${git_branch}\033[00m"
[ -n "$ctx_info" ] && out="${out} · ${ctx_info}"

printf "%b" "$out"
