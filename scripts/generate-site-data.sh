#!/bin/bash
# Generate Site Data for Dashboard
# 默认只扫描仓库内公开内容；显式传 --include-local 才附加本机 Claude skills/plugins
# 输出统一的 JSON 数据到 site/data.json，供前端 Dashboard 使用
# site/data.json 会被 Git 跟踪，因此默认模式必须可复现且不读取本机私有目录

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT="${REPO_ROOT}/site/data.json"
CLAUDE_HOME="${HOME}/.claude"
INCLUDE_LOCAL=0

case "${1:-}" in
  "") ;;
  --repo-only) INCLUDE_LOCAL=0 ;;
  --include-local) INCLUDE_LOCAL=1 ;;
  --help)
    echo "Usage: $0 [--repo-only|--include-local]"
    echo "  --repo-only     Scan only repository sources (default; safe for CI/public data)."
    echo "  --include-local Also include local Claude skills and plugins for private inspection."
    exit 0
    ;;
  *)
    echo "Unknown option: $1" >&2
    echo "Usage: $0 [--repo-only|--include-local]" >&2
    exit 2
    ;;
esac

TMPDIR_DATA=$(mktemp -d)
trap 'rm -rf "$TMPDIR_DATA"' EXIT

# ─── 辅助函数 ───

# 从 Markdown 文件提取 YAML frontmatter 指定字段
get_frontmatter_field() {
  local file="$1"
  local field="$2"
  sed -n '/^---$/,/^---$/p' "$file" | grep "^${field}:" | head -1 | sed "s/^${field}:[[:space:]]*//" || true
}

# 读取 frontmatter 之后的正文
get_content_after_frontmatter() {
  local file="$1"
  # Skip everything up to and including the second ---
  awk 'BEGIN{c=0} /^---$/{c++; next} c>=2{print}' "$file"
}

# 用 jq 转义字符串为合法 JSON string
json_escape() {
  printf '%s' "$1" | jq -Rs .
}

# ─── Skills 扫描 ───
# 扫描三个来源：仓库 skills/、本地 ~/.claude/skills/、已安装插件 skills

skills_dir="$TMPDIR_DATA/skills"
mkdir -p "$skills_dir"
skill_idx=0
seen_skills_file="$TMPDIR_DATA/seen_skills.txt"
touch "$seen_skills_file"

scan_skill() {
  local skill_file="$1"
  local source_label="$2"
  local display_path="$3"

  local name description version
  name=$(get_frontmatter_field "$skill_file" "name")
  [ -z "$name" ] && return
  description=$(get_frontmatter_field "$skill_file" "description")
  version=$(get_frontmatter_field "$skill_file" "version")

  # 去重：同名 skill 只保留第一个
  if grep -qFx "$name" "$seen_skills_file" 2>/dev/null; then
    return
  fi
  echo "$name" >> "$seen_skills_file"

  get_content_after_frontmatter "$skill_file" > "$TMPDIR_DATA/tmp_content"

  jq -n \
    --arg name "$name" \
    --arg description "$description" \
    --arg version "$version" \
    --arg source "$source_label" \
    --arg file "$display_path" \
    --rawfile content "$TMPDIR_DATA/tmp_content" \
    '{name: $name, description: $description, version: $version, source: $source, file: $file, content: $content}' \
    > "$skills_dir/$skill_idx.json"
  skill_idx=$((skill_idx + 1))
}

# 1) 本地自定义 skills (~/.claude/skills/)
# 注意：跳过 lark-* 等第三方 skill（npx skills 装的，symlink 到 ~/.agents，CI 环境没有，
# 会导致线上/本地数据不一致）。第三方清单改由 claude/configs/recommended-skills.json 记录。
if [ "$INCLUDE_LOCAL" -eq 1 ] && [ -d "${CLAUDE_HOME}/skills" ]; then
  while IFS= read -r skill_file; do
    local_name=$(get_frontmatter_field "$skill_file" "name")
    case "$local_name" in
      lark-*) continue ;;
    esac
    scan_skill "$skill_file" "local" "~/.claude/skills/${local_name}/SKILL.md"
  done < <(find -L "${CLAUDE_HOME}/skills" -name "SKILL.md" 2>/dev/null)
fi

# 2) 仓库 claude/skills/
while IFS= read -r skill_file; do
  rel_path="${skill_file#${REPO_ROOT}/}"
  slash_count=$(echo "$rel_path" | tr -cd '/' | wc -c | tr -d ' ')
  # rel_path 形如 claude/skills/<marketplace>/<name>/SKILL.md（≥4 个斜杠）
  if [ "$slash_count" -ge 4 ]; then
    source_label=$(echo "$rel_path" | cut -d'/' -f3)
  else
    source_label="custom"
  fi
  scan_skill "$skill_file" "$source_label" "$rel_path"
done < <(find "${REPO_ROOT}/claude/skills" -name "SKILL.md" -not -path "*/examples/*" 2>/dev/null)

# 2b) 仓库 skills/hzb-skills/ — 自建跨工具 skill marketplace（source 标 hzb）
# 含密 skill（g1-robot/wlcb-dev）的真身 SKILL.md 被 .gitignore 保护、正文含真实凭证，
# 扫描其脱敏版 SKILL.md.example 代替，保证 dashboard 能展示但不泄漏。
while IFS= read -r skill_file; do
  [ -f "${skill_file}.example" ] && continue   # 有脱敏兄弟文件的真身 → 跳过，改扫 .example
  rel_path="${skill_file#${REPO_ROOT}/}"
  scan_skill "$skill_file" "hzb" "$rel_path"
done < <(find "${REPO_ROOT}/skills/hzb-skills" -name "SKILL.md" -not -path "*/examples/*" 2>/dev/null)
# 脱敏版 SKILL.md.example（含密 skill 的可公开版本）
while IFS= read -r example_file; do
  skill_file="${example_file%.example}"
  rel_path="${skill_file#${REPO_ROOT}/}"
  scan_skill "$example_file" "hzb" "$rel_path"
done < <(find "${REPO_ROOT}/skills/hzb-skills" -name "SKILL.md.example" -not -path "*/examples/*" 2>/dev/null)

# 3) 已安装插件 skills (~/.claude/plugins/marketplaces/*)
# 只扫 Claude Code 标准路径下的 skills/ 目录，避免 .cursor/.gemini 等副本
if [ "$INCLUDE_LOCAL" -eq 1 ] && [ -d "${CLAUDE_HOME}/plugins/marketplaces" ]; then
  while IFS= read -r skill_file; do
    # 跳过非 Claude Code 标准路径（.cursor, .gemini, .codex 等）
    if echo "$skill_file" | grep -qE '/\.(cursor|gemini|codex|mastracode|continue|opencode|factory|codebuddy|pi)/'; then
      continue
    fi

    # 从路径提取插件名: marketplaces/<marketplace>/<...>/skills/<name>/SKILL.md
    mp_rel="${skill_file#${CLAUDE_HOME}/plugins/marketplaces/}"
    marketplace_name=$(echo "$mp_rel" | cut -d'/' -f1)

    scan_skill "$skill_file" "$marketplace_name" "plugin: $mp_rel"
  done < <(find "${CLAUDE_HOME}/plugins/marketplaces" -name "SKILL.md" -not -path "*/examples/*" -not -path "*/template/*" 2>/dev/null)
fi

# 合并所有 skill JSON 对象为数组
if ls "$skills_dir"/*.json >/dev/null 2>&1; then
  skills_json=$(jq -s '.' "$skills_dir"/*.json)
else
  skills_json="[]"
fi

# ─── Hooks 扫描 ───

hooks_dir="$TMPDIR_DATA/hooks"
mkdir -p "$hooks_dir"
hook_idx=0

while IFS= read -r hook_file; do
  rel_path="${hook_file#${REPO_ROOT}/}"
  filename=$(basename "$hook_file" .json)
  events=$(jq -c '[.hooks | keys[]]' "$hook_file" 2>/dev/null || echo '[]')
  description=$(jq -r '.description // ""' "$hook_file" 2>/dev/null || echo "")
  cat "$hook_file" > "$TMPDIR_DATA/tmp_content"

  jq -n \
    --arg name "$filename" \
    --arg file "$rel_path" \
    --arg description "$description" \
    --argjson events "$events" \
    --rawfile content "$TMPDIR_DATA/tmp_content" \
    '{name: $name, file: $file, description: $description, events: $events, content: $content}' \
    > "$hooks_dir/$hook_idx.json"
  hook_idx=$((hook_idx + 1))

done < <(find "${REPO_ROOT}/claude/hooks" -name "*.json" -not -path "*/examples/*" 2>/dev/null)

if ls "$hooks_dir"/*.json >/dev/null 2>&1; then
  hooks_json=$(jq -s '.' "$hooks_dir"/*.json)
else
  hooks_json="[]"
fi

# ─── Configs 扫描 ───

configs_dir="$TMPDIR_DATA/configs"
mkdir -p "$configs_dir"
config_idx=0

for config_file in "${REPO_ROOT}"/claude/configs/*.json "${REPO_ROOT}"/claude/configs/*.md; do
  [ -f "$config_file" ] || continue
  rel_path="${config_file#${REPO_ROOT}/}"
  filename=$(basename "$config_file")
  case "$filename" in
    *.bak|*.bak-*|*.local.json|settings.local.json|settings.glm.json|settings.windows.local.json)
      continue
      ;;
  esac
  if git -C "$REPO_ROOT" check-ignore -q "$rel_path" 2>/dev/null; then
    continue
  fi
  cat "$config_file" > "$TMPDIR_DATA/tmp_content"

  # 提取 JSON 配置文件的元数据摘要
  config_meta="{}"
  if [[ "$filename" == *.json ]] && jq empty "$config_file" 2>/dev/null; then
    config_meta=$(jq -c '{
      keys: [keys[] | select(. != null)] | length,
      has_hooks: (has("hooks") // false),
      has_plugins: (has("enabledPlugins") // false),
      model: (.model // null),
      plugin_count: (if .enabledPlugins then (.enabledPlugins | keys | length) else 0 end),
      hook_event_count: (if .hooks then (.hooks | keys | length) else 0 end)
    }' "$config_file" 2>/dev/null || echo '{}')
  fi

  jq -n \
    --arg name "$filename" \
    --arg file "$rel_path" \
    --argjson meta "$config_meta" \
    --rawfile content "$TMPDIR_DATA/tmp_content" \
    '{name: $name, file: $file, meta: $meta, content: $content}' \
    > "$configs_dir/$config_idx.json"
  config_idx=$((config_idx + 1))
done

if ls "$configs_dir"/*.json >/dev/null 2>&1; then
  configs_json=$(jq -s '.' "$configs_dir"/*.json)
else
  configs_json="[]"
fi

# ─── Scripts 扫描 ───

scripts_json="[]"
total_scripts_lines=0

for script_file in "${REPO_ROOT}"/scripts/*.sh "${REPO_ROOT}"/claude/scripts/*.sh; do
  [ -f "$script_file" ] || continue
  filename=$(basename "$script_file")

  # 跳过自身和 export-memory.sh
  if [ "$filename" = "generate-site-data.sh" ] || [ "$filename" = "export-memory.sh" ]; then
    continue
  fi

  rel_path="${script_file#${REPO_ROOT}/}"
  lines=$(wc -l < "$script_file")
  total_scripts_lines=$((total_scripts_lines + lines))

  # 提取第2-4行注释作为描述
  description=$(sed -n '2,4p' "$script_file" | grep '^#' | sed 's/^#[[:space:]]*//' | tr '\n' ' ' | sed 's/[[:space:]]*$//')

  # 从注释中提取依赖列表 (requires/depends: jq, curl, tmux 等)
  deps=$(grep -i 'requires\|depends\|依赖' "$script_file" | head -3 | sed 's/^#[[:space:]]*//' | tr '\n' ' ' | sed 's/[[:space:]]*$//' || true)

  scripts_json=$(jq -n \
    --argjson arr "$scripts_json" \
    --arg name "$filename" \
    --arg file "$rel_path" \
    --arg description "$description" \
    --argjson lines "$lines" \
    --arg deps "$deps" \
    '$arr + [{name: $name, file: $file, description: $description, lines: $lines, deps: $deps}]'
  )
done

# ─── Commands 扫描 ───

commands_dir_data="$TMPDIR_DATA/commands"
mkdir -p "$commands_dir_data"
cmd_idx=0

for cmd_file in "${REPO_ROOT}"/claude/commands/*.md "${REPO_ROOT}"/skills/hzb-skills/plugins/hzb/commands/*.md; do
  [ -f "$cmd_file" ] || continue
  filename=$(basename "$cmd_file")
  [ "$filename" = "README.md" ] && continue

  # 跳过含密真身（有对应 .example 的文件被 .gitignore 保护，不应进 data.json）
  [ -f "${cmd_file}.example" ] && continue

  rel_path="${cmd_file#${REPO_ROOT}/}"
  cmd_name="${filename%.md}"

  # 提取第一行标题作为描述
  description=$(head -1 "$cmd_file" | sed 's/^#[[:space:]]*//')
  lines=$(wc -l < "$cmd_file")

  cat "$cmd_file" > "$TMPDIR_DATA/tmp_content"

  jq -n \
    --arg name "$cmd_name" \
    --arg file "$rel_path" \
    --arg description "$description" \
    --argjson lines "$lines" \
    --rawfile content "$TMPDIR_DATA/tmp_content" \
    '{name: $name, file: $file, description: $description, lines: $lines, content: $content}' \
    > "$commands_dir_data/$cmd_idx.json"
  cmd_idx=$((cmd_idx + 1))
done

if ls "$commands_dir_data"/*.json >/dev/null 2>&1; then
  commands_json=$(jq -s '.' "$commands_dir_data"/*.json)
else
  commands_json="[]"
fi

# ─── Plugins 扫描 ───

plugins_json="[]"
plugins_file="${REPO_ROOT}/claude/configs/recommended-plugins.json"
if [ -f "$plugins_file" ]; then
  plugins_json=$(jq '.plugins' "$plugins_file" 2>/dev/null || echo '[]')
fi

# ─── Recommended Skills 清单（第三方 / 官方 skill 安装清单）───

recommended_skills_json="[]"
rec_skills_file="${REPO_ROOT}/claude/configs/recommended-skills.json"
if [ -f "$rec_skills_file" ]; then
  recommended_skills_json=$(jq '.skills' "$rec_skills_file" 2>/dev/null || echo '[]')
fi

# ─── VERIFY.md 解析 ───

verify_pending="[]"
verify_verified="[]"
verify_deprecated="[]"

current_section=""
current_entry=""
current_title=""
current_commit=""
current_date=""
current_status=""
current_method=""
current_expected=""
current_actual=""
current_reason=""

flush_entry() {
  if [ -z "$current_title" ]; then
    return
  fi

  local target_arr
  case "$current_section" in
    pending)    target_arr="verify_pending" ;;
    verified)   target_arr="verify_verified" ;;
    deprecated) target_arr="verify_deprecated" ;;
    *) return ;;
  esac

  local entry
  entry=$(jq -n \
    --arg title "$current_title" \
    --arg commit "$current_commit" \
    --arg date "$current_date" \
    --arg status "$current_status" \
    --arg method "$current_method" \
    --arg expected "$current_expected" \
    --arg actual "$current_actual" \
    --arg reason "$current_reason" \
    '{title: $title, commit: $commit, date: $date, status: $status, method: $method, expected: $expected, actual: $actual, reason: $reason}'
  )

  case "$current_section" in
    pending)    verify_pending=$(jq --argjson arr "$verify_pending" --argjson entry "$entry" -n '$arr + [$entry]') ;;
    verified)   verify_verified=$(jq --argjson arr "$verify_verified" --argjson entry "$entry" -n '$arr + [$entry]') ;;
    deprecated) verify_deprecated=$(jq --argjson arr "$verify_deprecated" --argjson entry "$entry" -n '$arr + [$entry]') ;;
  esac

  # Reset entry fields
  current_title=""
  current_commit=""
  current_date=""
  current_status=""
  current_method=""
  current_expected=""
  current_actual=""
  current_reason=""
}

verify_file="${REPO_ROOT}/VERIFY.md"
in_comment=false
if [ -f "$verify_file" ]; then
  while IFS= read -r line; do
    # Skip HTML comments
    if [[ "$line" =~ \<\!-- ]]; then
      in_comment=true
      # Check if comment closes on same line
      [[ "$line" =~ --\> ]] && in_comment=false
      continue
    fi
    if $in_comment; then
      [[ "$line" =~ --\> ]] && in_comment=false
      continue
    fi

    # 检测 section 标题
    if [[ "$line" =~ ^##[[:space:]].*(Pending|Current[[:space:]]Manual[[:space:]]Verification|当前人工验收) ]]; then
      flush_entry
      current_section="pending"
      continue
    elif [[ "$line" =~ ^##[[:space:]].*Verified ]]; then
      flush_entry
      current_section="verified"
      continue
    elif [[ "$line" =~ ^##[[:space:]].*Deprecated ]]; then
      flush_entry
      current_section="deprecated"
      continue
    elif [[ "$line" =~ ^##[[:space:]] ]] && [[ ! "$line" =~ Pending|Verified|Deprecated|Current[[:space:]]Manual[[:space:]]Verification|当前人工验收 ]]; then
      # Other section headers (e.g., How It Works, Status Legend) — skip
      flush_entry
      current_section=""
      continue
    fi

    # Skip if not in a valid section
    [ -z "$current_section" ] && continue

    # 解析条目行: - [ ] **标题** (commit: xxx, date: YYYY-MM-DD)
    #             - [x] **标题** (commit: xxx, date: YYYY-MM-DD)
    #             - [-] **标题** (date: YYYY-MM-DD)
    if [[ "$line" =~ ^-[[:space:]]\[(.)\][[:space:]]\*\*(.+)\*\*[[:space:]]*\((.+)\) ]]; then
      flush_entry
      local_marker="${BASH_REMATCH[1]}"
      current_title="${BASH_REMATCH[2]}"
      local_meta="${BASH_REMATCH[3]}"

      case "$local_marker" in
        " ") current_status="pending"; current_section="pending" ;;
        "x") current_status="verified"; current_section="verified" ;;
        "-") current_status="deprecated"; current_section="deprecated" ;;
        *)   current_status="unknown"; current_section="" ;;
      esac

      # Extract commit and date from meta
      if [[ "$local_meta" =~ commit:[[:space:]]*([^,]+) ]]; then
        current_commit="${BASH_REMATCH[1]}"
        # Trim trailing spaces
        current_commit="${current_commit%"${current_commit##*[![:space:]]}"}"
      fi
      if [[ "$local_meta" =~ date:[[:space:]]*([0-9-]+) ]]; then
        current_date="${BASH_REMATCH[1]}"
      fi
      continue
    fi

    # 解析子字段
    if [[ "$line" =~ ^[[:space:]]+-[[:space:]]验证方法：(.*) ]]; then
      current_method="${BASH_REMATCH[1]}"
    elif [[ "$line" =~ ^[[:space:]]+-[[:space:]]预期效果：(.*) ]]; then
      current_expected="${BASH_REMATCH[1]}"
    elif [[ "$line" =~ ^[[:space:]]+-[[:space:]]实际效果：(.*) ]]; then
      current_actual="${BASH_REMATCH[1]}"
    elif [[ "$line" =~ ^[[:space:]]+-[[:space:]]原因：(.*) ]]; then
      current_reason="${BASH_REMATCH[1]}"
    fi

  done < "$verify_file"
  # Flush last entry
  flush_entry
fi

# ─── 统计数据 ───

total_skills=$(echo "$skills_json" | jq 'length')
total_hooks=$(echo "$hooks_json" | jq 'length')
total_configs=$(echo "$configs_json" | jq 'length')
total_scripts=$(echo "$scripts_json" | jq 'length')
total_plugins=$(echo "$plugins_json" | jq 'length')
total_recommended_skills=$(echo "$recommended_skills_json" | jq 'length')
total_commands=$(echo "$commands_json" | jq 'length')
total_verified=$(echo "$verify_verified" | jq 'length')
total_pending=$(echo "$verify_pending" | jq 'length')
total_deprecated=$(echo "$verify_deprecated" | jq 'length')
manifest_file="${REPO_ROOT}/config/manifest.json"
if [ -f "$manifest_file" ]; then
  inventory_dir="$TMPDIR_DATA/inventory"
  mkdir -p "$inventory_dir"
  inventory_idx=0
  while IFS= read -r resource; do
    selected_source=""
    while IFS= read -r candidate; do
      [ -n "$candidate" ] || continue
      if [ -e "${REPO_ROOT}/${candidate}" ] && [ -n "$(git -C "$REPO_ROOT" ls-files -- "$candidate")" ]; then
        selected_source="$candidate"
        break
      fi
    done < <(echo "$resource" | jq -r 'if .source then [.source][] else .sourceCandidates[] end')

    content_file=""
    if [ -n "$selected_source" ] && [ -f "${REPO_ROOT}/${selected_source}" ]; then
      content_file="$selected_source"
    elif [ -n "$selected_source" ] && [ -d "${REPO_ROOT}/${selected_source}" ]; then
      for nested in SKILL.md SKILL.md.example README.md .claude-plugin/marketplace.json; do
        candidate="${selected_source}/${nested}"
        if [ -f "${REPO_ROOT}/${candidate}" ] && git -C "$REPO_ROOT" ls-files --error-unmatch -- "$candidate" >/dev/null 2>&1; then
          content_file="$candidate"
          break
        fi
      done
    fi

    : > "$TMPDIR_DATA/tmp_inventory_content"
    if [ -n "$content_file" ]; then
      cat "${REPO_ROOT}/${content_file}" > "$TMPDIR_DATA/tmp_inventory_content"
    fi
    jq -n \
      --argjson resource "$resource" \
      --arg resolved_source "$selected_source" \
      --arg content_file "$content_file" \
      --rawfile content "$TMPDIR_DATA/tmp_inventory_content" \
      '$resource + {
        status: "desired",
        action: "none",
        resolvedSource: $resolved_source,
        contentFile: $content_file,
        content: $content
      }' > "$inventory_dir/$inventory_idx.json"
    inventory_idx=$((inventory_idx + 1))
  done < <(jq -c '.resources[]' "$manifest_file")
  inventory_resources=$(jq -s '.' "$inventory_dir"/*.json)
  inventory_version=$(jq '.version' "$manifest_file")
  inventory_json=$(jq -n \
    --argjson version "$inventory_version" \
    --argjson resources "$inventory_resources" \
    '{mode: "desired", version: $version, resources: $resources}')
else
  inventory_json='{"mode":"desired","version":1,"resources":[]}'
fi
total_resources=$(echo "$inventory_json" | jq '.resources | length')

# Git info
git_branch=$(cd "$REPO_ROOT" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
git_commit=$(cd "$REPO_ROOT" && git rev-parse --short HEAD 2>/dev/null || echo "unknown")
generated_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ─── 组装最终 JSON ───

mkdir -p "${REPO_ROOT}/site"

# 将各数组写入临时文件，避免 --argjson 参数列表过长
echo "$skills_json" > "$TMPDIR_DATA/skills.json"
echo "$hooks_json" > "$TMPDIR_DATA/hooks.json"
echo "$configs_json" > "$TMPDIR_DATA/configs.json"
echo "$scripts_json" > "$TMPDIR_DATA/scripts.json"
echo "$plugins_json" > "$TMPDIR_DATA/plugins.json"
echo "$recommended_skills_json" > "$TMPDIR_DATA/recommended_skills.json"
echo "$commands_json" > "$TMPDIR_DATA/commands.json"
echo "$verify_pending" > "$TMPDIR_DATA/verify_pending.json"
echo "$verify_verified" > "$TMPDIR_DATA/verify_verified.json"
echo "$verify_deprecated" > "$TMPDIR_DATA/verify_deprecated.json"
echo "$inventory_json" > "$TMPDIR_DATA/inventory.json"

jq -n \
  --slurpfile skills "$TMPDIR_DATA/skills.json" \
  --slurpfile hooks "$TMPDIR_DATA/hooks.json" \
  --slurpfile configs "$TMPDIR_DATA/configs.json" \
  --slurpfile scripts_arr "$TMPDIR_DATA/scripts.json" \
  --slurpfile plugins "$TMPDIR_DATA/plugins.json" \
  --slurpfile recommended_skills "$TMPDIR_DATA/recommended_skills.json" \
  --slurpfile commands "$TMPDIR_DATA/commands.json" \
  --slurpfile vp "$TMPDIR_DATA/verify_pending.json" \
  --slurpfile vv "$TMPDIR_DATA/verify_verified.json" \
  --slurpfile vd "$TMPDIR_DATA/verify_deprecated.json" \
  --slurpfile inventory "$TMPDIR_DATA/inventory.json" \
  --argjson total_skills "$total_skills" \
  --argjson total_hooks "$total_hooks" \
  --argjson total_configs "$total_configs" \
  --argjson total_scripts "$total_scripts" \
  --argjson total_plugins "$total_plugins" \
  --argjson total_recommended_skills "$total_recommended_skills" \
  --argjson total_commands "$total_commands" \
  --argjson total_scripts_lines "$total_scripts_lines" \
  --argjson total_verified "$total_verified" \
  --argjson total_pending "$total_pending" \
  --argjson total_deprecated "$total_deprecated" \
  --argjson total_resources "$total_resources" \
  --arg git_branch "$git_branch" \
  --arg git_commit "$git_commit" \
  --arg generated_at "$generated_at" \
  '{
    stats: {
      total_skills: $total_skills,
      total_hooks: $total_hooks,
      total_configs: $total_configs,
      total_scripts: $total_scripts,
      total_plugins: $total_plugins,
      total_recommended_skills: $total_recommended_skills,
      total_commands: $total_commands,
      total_scripts_lines: $total_scripts_lines,
      total_verified: $total_verified,
      total_pending: $total_pending,
      total_deprecated: $total_deprecated,
      total_resources: $total_resources
    },
    git: {
      branch: $git_branch,
      commit: $git_commit
    },
    generated_at: $generated_at,
    skills: $skills[0],
    hooks: $hooks[0],
    configs: $configs[0],
    scripts: $scripts_arr[0],
    plugins: $plugins[0],
    recommended_skills: $recommended_skills[0],
    commands: $commands[0],
    inventory: $inventory[0],
    verify: {
      pending: $vp[0],
      verified: $vv[0],
      deprecated: $vd[0]
    }
  }' > "$OUTPUT"

echo "Generated: $OUTPUT"
echo "Stats: skills=$total_skills hooks=$total_hooks configs=$total_configs scripts=$total_scripts commands=$total_commands plugins=$total_plugins"
echo "Verify: pending=$total_pending verified=$total_verified deprecated=$total_deprecated"
