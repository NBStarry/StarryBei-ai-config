#!/usr/bin/env bash
# HEIC → JPEG 批量转换（macOS sips，无依赖）
#
# 用法:
#   ./heic_to_jpg.sh <src_dir> <dst_dir> [max_long_edge_px]
#
# 默认 max_long_edge_px=1600（平衡可读性 + 上传体积）
# 转换后文件名保持一致（.HEIC -> .jpg）
#
# 设计取舍:
#   - 用 sips 不用 imagemagick：macOS 自带，零部署成本
#   - 1600px 长边：飞书文档显示宽度 ~800-1000px，1600px 2x retina 够用
#   - 不删原 HEIC：万一画质损失要回滚

set -e

SRC="${1:?usage: $0 <src_dir> <dst_dir> [max_long_edge_px]}"
DST="${2:?usage: $0 <src_dir> <dst_dir> [max_long_edge_px]}"
MAX="${3:-1600}"

if [ ! -d "$SRC" ]; then
  echo "error: source directory not found: $SRC" >&2
  exit 1
fi

mkdir -p "$DST"
COUNT=0
SKIPPED=0
for h in "$SRC"/*.HEIC "$SRC"/*.heic; do
  [ -f "$h" ] || continue
  name=$(basename "$h")
  name="${name%.HEIC}"
  name="${name%.heic}"
  out="$DST/${name}.jpg"
  if [ -f "$out" ]; then
    SKIPPED=$((SKIPPED+1))
    continue
  fi
  sips -s format jpeg -Z "$MAX" "$h" --out "$out" >/dev/null 2>&1
  COUNT=$((COUNT+1))
done

echo "Converted $COUNT HEIC → JPG (skipped $SKIPPED already existing) → $DST"
