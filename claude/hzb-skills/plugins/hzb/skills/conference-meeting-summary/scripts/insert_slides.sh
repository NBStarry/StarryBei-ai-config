#!/usr/bin/env bash
# 反向序嵌入 slide 照片到飞书文档
#
# 用法（复制这个文件改成你自己的 mapping）:
#   1) 准备好文档（已 docs +create），拿到 URL
#   2) 把照片转好 JPG，放在一个目录
#   3) 编辑下面的 ins() 调用：每行 ins "<img>" "<anchor 唯一文字>" "<caption>" ["--before"]
#   4) 同章节多张时，**最后想显示的照片最先 ins**（反向序）
#   5) cd 到照片目录（lark-cli 安全检查要求 --file 是相对路径），bash 跑本脚本
#
# 底层逻辑:
#   docs +media-insert --selection-with-ellipsis "X" 把图插到 X 所在 block 之后。
#   多次插入同一锚点时，新图顶到锚点紧下面，旧图被推下去 → 因此反向序。
#
# 已知陷阱（写在 SKILL.md 里也有，再强调一次）:
#   - media-insert 不支持 --api-version（v2 是其他指令的）
#   - --file 必须相对路径，否则被 lark-cli 安全规则拦
#   - image caption 是 block 属性，不在 markdown 视图，**不能**作为下一张图的锚点
#   - 用 --before 时，锚点是"后继 block"的文本，图会插在该 block 之前

set -e

# === 改这两行 ===
DOC="${DOC:?export DOC=https://...feishu.cn/docx/<token> first}"
PROFILE_ARGS="${PROFILE_ARGS:---profile jushen-team --as bot}"

PASS=0; FAIL=0; FAILS=()

ins() {
  local IMG="$1"; local ANCHOR="$2"; local CAP="$3"; local EXTRA="$4"
  local OUT
  OUT=$(lark-cli docs +media-insert $PROFILE_ARGS \
    --doc "$DOC" \
    --file "./$IMG" \
    --type image \
    --selection-with-ellipsis "$ANCHOR" \
    --align center \
    --caption "$CAP" $EXTRA 2>&1)
  if echo "$OUT" | grep -q '"ok": true'; then
    echo "OK   $IMG"
    PASS=$((PASS+1))
  else
    echo "FAIL $IMG  anchor='$ANCHOR'"
    echo "$OUT" | grep -E "message|error" | head -2
    FAIL=$((FAIL+1)); FAILS+=("$IMG")
  fi
}

# === 范例 mapping（按你自己的会议改）===
#
# # Section A — 单张图
# ins "IMG_0001.jpg" "## 1. 章节标题" "slide: <什么内容>"
#
# # Section B — 三张图，按时间序 a/b/c 显示
# # 反向插入，最后想显示的 c 先插
# ins "IMG_0004.jpg" "## 2. 章节标题" "slide: c 内容"
# ins "IMG_0003.jpg" "## 2. 章节标题" "slide: b 内容"
# ins "IMG_0002.jpg" "## 2. 章节标题" "slide: a 内容"

echo ""
echo "=== SUMMARY: PASS=$PASS FAIL=$FAIL ==="
[ $FAIL -gt 0 ] && echo "Failed: ${FAILS[*]}"
