// 钉钉闪记 (shanji.dingtalk.com/app/transcribes/...) 转写 + AI Summary 抽取
//
// 用法（通过 web-access CDP Proxy）:
//   TARGET=$(curl -s "http://localhost:3456/new?url=<SHANJI_URL>" | jq -r .targetId)
//   sleep 3-4  # 等 React fiber 挂载
//   curl -s -X POST "http://localhost:3456/eval?target=$TARGET" \
//     --data-binary @"$CONFERENCE_SKILL_DIR/scripts/extract_shanji.js"
//
// 返回 JSON:
//   {
//     title: "<doc title>",
//     paragraphCount: <int>,
//     foundIdx: <0/1/.../-2>,    // -2 表示走的 body fiber DFS 兜底
//     durationMs: <int>,
//     firstStart: <int>,
//     transcript: "<带 [mm:ss] Speaker: 格式的多段拼接>",
//     aiSummary: "<钉钉自动生成纪要原文，含错别字>",
//     transcriptLen, aiSummaryLen
//   }
//
// 底层原理：
//   钉钉闪记用 react-window VariableSizeList 虚拟化渲染，innerText 永远只有可见的 7-10 段。
//   但 React 组件 props 上挂了完整的 paragraphs 数组（126 段全在内存），从滚动容器
//   的 fiber 往上走树就能找到含 paragraphs 属性的 anon 节点。
//
// v2 升级（2026-05-18, 因 A1 seg1 超短录音失败回流）:
//   v1 假设 scrollables[0] 就是 transcript 容器，但对于"超短录音 + 段数少"或
//   "AI Summary 比 transcript 高"等场景，scrollables[0] 可能不是 transcript。
//   v2 改为对每个 scrollable 都试 fiber 走树，全失败再走 document.body fiber DFS 兜底。
//
// 已知陷阱:
//   - 页面加载未完成时 paragraphs 找不到 — sleep 长点（>=3-4s）再 eval
//   - 偶发 AI Summary 容器 .fm-full-text-summary 在 scrollables 之外 —— v2 用
//     document.querySelector 全文档搜，再 fallback 到 scrollables 局部搜

(() => {
  const fmt = (ms) => {
    const s = Math.floor(ms / 1000);
    const m = Math.floor(s / 60);
    const r = s % 60;
    return String(m).padStart(2,'0') + ':' + String(r).padStart(2,'0');
  };

  // 找所有滚动容器（注意：不加 +50 阈值，超短录音容器 scrollHeight ≈ clientHeight）
  const scrollables = [];
  document.querySelectorAll("*").forEach(el => {
    const s = getComputedStyle(el);
    if ((s.overflowY === "auto" || s.overflowY === "scroll") && el.scrollHeight > el.clientHeight) {
      scrollables.push(el);
    }
  });

  // 路径 1: 对每个 scrollable 都尝试 fiber 走树（不只 scrollables[0]）
  let paragraphs = null;
  let foundIdx = -1;
  for (let i = 0; i < scrollables.length; i++) {
    const el = scrollables[i];
    const fk = Object.keys(el).find(k => k.startsWith("__reactFiber"));
    if (!fk) continue;
    let f = el[fk], depth = 0;
    while (f && depth < 50) {
      if (f.memoizedProps && Array.isArray(f.memoizedProps.paragraphs)) {
        paragraphs = f.memoizedProps.paragraphs;
        foundIdx = i;
        break;
      }
      f = f.return;
      depth++;
    }
    if (paragraphs) break;
  }

  // 路径 2: 兜底 — 从 document.body 做 fiber DFS
  if (!paragraphs) {
    const root = document.body;
    function walk(fiber, depth) {
      if (!fiber || depth > 200) return null;
      if (fiber.memoizedProps && Array.isArray(fiber.memoizedProps.paragraphs)) return fiber.memoizedProps.paragraphs;
      if (fiber.child) {
        const r = walk(fiber.child, depth + 1);
        if (r) return r;
      }
      if (fiber.sibling) {
        const r = walk(fiber.sibling, depth + 1);
        if (r) return r;
      }
      return null;
    }
    const allKeys = Object.keys(root);
    for (const k of allKeys) {
      if (k.startsWith("__reactContainer") || k.startsWith("__reactFiber")) {
        const fiber = root[k];
        if (fiber) {
          const r = walk(fiber.stateNode ? fiber.stateNode.current : fiber, 0);
          if (r) { paragraphs = r; foundIdx = -2; break; }
        }
      }
    }
  }

  if (!paragraphs) {
    return {
      error: "no paragraphs found",
      scrollables: scrollables.length,
      info: scrollables.map(e => ({tag: e.tagName, cls: (e.className || "").toString().slice(0, 100), len: e.innerText.length}))
    };
  }

  // 拼 transcript：[mm:ss] Speaker N: 内容
  const lines = paragraphs.map(p => {
    const sp = (p.speakerDisplayModel && p.speakerDisplayModel.nickName) || p.nickName || p.speakerId || "?";
    return `[${fmt(p.startTime)}] ${sp}: ${p.paragraph}`;
  });
  const transcript = lines.join("\n\n");

  // AI Summary（容器可能在 scrollables 之外）
  let aiSummary = "";
  const aiEl = document.querySelector(".fm-full-text-summary");
  if (aiEl) {
    aiSummary = aiEl.innerText;
  } else {
    for (const s of scrollables) {
      const sub = s.querySelector(".fm-full-text-summary");
      if (sub) { aiSummary = sub.innerText; break; }
    }
  }

  return {
    title: document.title,
    paragraphCount: paragraphs.length,
    foundIdx,
    durationMs: paragraphs[paragraphs.length - 1].endTime,
    firstStart: paragraphs[0].startTime,
    transcript,
    aiSummary,
    transcriptLen: transcript.length,
    aiSummaryLen: aiSummary.length
  };
})()
