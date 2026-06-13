---
domain: meeting.tencent.com
aliases: [腾讯会议, Tencent Meeting]
updated: 2026-06-10
---
## 平台特征
- 分享链接形如 `meeting.tencent.com/ct/<token>`，落地页是「录制文件」卡片，只有一个「前往查看」button，点击后**新开 tab**（同 URL，title 变「转写文件」）——要去 /targets 里找新 tab。
- 转写页未登录也能读（2026-06-10 验证）：智能总结（纪要）直接在 body innerText 里全量可取；逐字稿是**虚拟列表**，容器 `.minutes-module-list`，只渲染可视区。

## 有效模式
- 智能总结：直接 `document.body.innerText`，含会议主题/摘要/分章节/待办。
- 逐字稿全量提取：循环 eval——每次 `list.scrollTop += 450`（视口约 400px，450 步长实测无漏条）+ 解析 innerText 的 `speaker\n时间戳\n内容` 三元组，按 `时间戳|内容前20字` 去重存 `window.__acc`（Map 保插入序=时间序）；`scrollHeight` 会边滚边长（1.5h 会议从 17k 涨到 31k px），done 判据 `scrollTop+clientHeight >= scrollHeight-5`；步间 sleep 0.4s。85 分钟会议 ≈ 274 条 / 2.7 万字。
- 完整性校验：时间戳应单调递增，>90s 间隔多为长独白或换人间隙。

## 已知陷阱
- 落地页 body 只有 53 字，别误判为空页/需登录——内容在点「前往查看」后的新 tab。
- 逐字稿直接取 innerText 只有当前视口 ~1k 字，必须滚动累积。
