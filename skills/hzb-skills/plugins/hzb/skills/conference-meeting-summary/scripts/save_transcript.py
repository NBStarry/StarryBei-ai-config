#!/usr/bin/env python3
"""把 extract_shanji.js 抽出来的 JSON 落盘成 txt。

Stdin / 文件参数读 JSON（含 transcript / aiSummary），写两个 txt 到指定目录。

用法:
    # 方式 1: pipe
    curl -X POST ... --data-binary @extract_shanji.js | python3 save_transcript.py \
        --code A2 \
        --out _extracted/

    # 方式 2: 文件
    python3 save_transcript.py --json dump.json --code A2 --out _extracted/

输出:
    <out>/<code>-转写原文.txt
    <out>/<code>-闪记纪要.txt
"""
import argparse, json, os, sys


def fmt_duration(ms: int) -> str:
    m = ms // 60000
    s = (ms % 60000) // 1000
    return f"{m}:{s:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="JSON 文件路径，省略则从 stdin 读")
    ap.add_argument("--code", required=True, help="会议代号（A2/B1 等），用于命名")
    ap.add_argument("--out", required=True, help="输出目录")
    args = ap.parse_args()

    raw = open(args.json).read() if args.json else sys.stdin.read()
    # CDP eval 返回的 JSON 外层是 {"value": "<json string>"} 或直接对象
    obj = json.loads(raw)
    if "value" in obj and isinstance(obj["value"], str):
        obj = json.loads(obj["value"])
    elif "value" in obj and isinstance(obj["value"], dict):
        obj = obj["value"]

    if "error" in obj:
        print(f"extract_shanji 报错: {obj['error']}", file=sys.stderr)
        sys.exit(2)

    os.makedirs(args.out, exist_ok=True)

    transcript_path = os.path.join(args.out, f"{args.code}-转写原文.txt")
    with open(transcript_path, "w") as f:
        f.write(f"# {obj['title']}\n")
        f.write(f"# 时长: {fmt_duration(obj['durationMs'])}  |  段数: {obj['paragraphCount']}\n")
        f.write("# 来源: 钉钉闪记自动转写（可能含语音识别错误，需与 slide 交叉校对）\n\n")
        f.write(obj["transcript"])

    summary_path = os.path.join(args.out, f"{args.code}-闪记纪要.txt")
    with open(summary_path, "w") as f:
        f.write(f"# {obj['title']} — 钉钉闪记自动生成 AI Summary（待与正文 diff）\n\n")
        f.write(obj.get("aiSummary", "<没有 AI Summary>"))

    print(f"written:\n  {transcript_path}  ({obj['transcriptLen']} chars)\n  {summary_path}  ({obj.get('aiSummaryLen', 0)} chars)")


if __name__ == "__main__":
    main()
