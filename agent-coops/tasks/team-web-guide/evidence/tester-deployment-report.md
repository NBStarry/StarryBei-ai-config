# Config 团队指南入口部署独立验证

## 目标与范围

本记录补充母任务 WG09 所需的公开构建产物与部署证据。测试者真实 Codex Session ID：`01a14484-7a7d-7cb0-9052-8142ac04bc3a`。本轮直接检查已上传的 github-pages 构建产物和 GitHub Pages 实际页面，不以仓库源码代替部署产物。

正式本地 test 版本保持 `6d50c8e42000a3d42d48ed6e3b412ee75ba7851986a0a5fbf6e4a264094fdf7e`。本记录不重发 product、plan 或 test，不修改生产源码。

## 计划与进展

[PR #2](https://github.com/NBStarry/StarryBei-ai-config/pull/2) 于 2026-10-16 13:45:47 UTC 合并到 dev，merge SHA 为 `c9085ce8a80d02aa2e5b21aa35d4df51ef8c47cb`。对应 [CI run 38910376947](https://github.com/NBStarry/StarryBei-ai-config/actions/runs/38910376947) 的 build、windows-validation 和 deploy 均成功。部署成功时刻为 13:46:46 UTC。

首次状态查询已返回 completed/success，因此没有继续轮询。测试者下载该 run 的实际 github-pages artifact，核对 API digest、归档文件与包内 workflow.html，并在 Chrome 检查公开旧地址、桌面及移动视口、返回导航和八个旧片段。浏览器主要观察时段为 13:50:00–13:52:55 UTC，即北京时间 21:50:00–21:52:55；逐项精确时刻见浏览器 JSON。

| 检查对象 | 观察结果 |
| --- | --- |
| github-pages artifact | ID `12049204718`，下载 ZIP 摘要与 GitHub API digest 一致，内部为 artifact.tar。 |
| 构建范围 | merge SHA 对应 workflow 上传 ./site。实际 tar 包含 9 个文件，没有 agent-coops、Team 目录、符号链接或路径越界项。 |
| workflow.html 内容 | 只含已确认迁移说明、权限提示和三个原生链接；无脚本、嵌入、自动跳转或 Team 私有正文。 |
| 公开基本地址 | [workflow.html](https://nbstarry.github.io/StarryBei-ai-config/workflow.html) 返回 200，显示已确认迁移页。 |
| 桌面与移动 | 实际 CSS 视口分别为 1280×900、390×844；scrollWidth 为 1272、382。文字和入口可读，无重叠、遮挡或横向溢出。 |
| 返回入口 | 测试者使用原生点击返回链接，实际进入 /StarryBei-ai-config/index.html，标题为 AI Config Dashboard。 |
| 旧片段 | overview、architecture、five-roles、example、checks、principles、operations、limits 均显示同一迁移卡片，且返回 href 均为 index.html。 |
| 资源边界 | 可见资源为两份同源 CSS、已有 Google Fonts CSS 和测试者的同源摘要 fetch；未观察到 Team 私有资源读取。 |

部署归档 ZIP SHA-256：`b495b809a967e5404de39b813974475f409fabbb51c131044b8f48967673967a`。

包内 artifact.tar SHA-256：`21625a3a963859d7edbc3df7d325661ba7ec904516bf65124856470ca2422d1e`。

包内页面、公开基本地址、两种视口和八个片段对应的 workflow.html SHA-256 均为 `00bdce81230230bff2e2444ce843273e101d56552d66a2a7a7150118f339e89d`，与正式本地 test 的源码摘要一致。

## 阻塞与决策

本轮部署层检查通过，没有发现需要返工的问题。导航至第一个旧片段时，浏览器工具曾超时。连接及目标状态恢复后，测试者在原标签中完成实际 DOM、摘要和八个片段核对；该超时没有被当作页面通过证据。

13:55:33 UTC 读回时，dev 已前移至 `aa88f4041ca16fef248cdad6b807067f66898487`。该提交由 github-actions[bot] 生成，父提交为本次 merge SHA，仅修改 site/data.json。Pages 本轮部署仍来自上述 CI run。main 保持 `819bbc4a1ad98b9fb657294806e1b06a1b269ebd`。

本记录支持 WG09 的构建产物与公开部署层事实。用户最终验收、私有 Team 指南内容和任意读者的仓库授权不属于本轮验证；这些项目仍需对应任务处理。测试者未提交、推送、合并或发送外部消息。

测试标签已关闭，临时视口覆盖已清除。实际 ZIP、tar 与提取页保存在 evidence/model-local/tester-deployment-38910376947/，该目录沿用已有忽略规则。

## 验收与证据

- [CI、实际 artifact 与部署记录](tester-deployment-artifact-checks.json)：包含 run、merge SHA、artifact 元数据、ZIP/tar 摘要、包内文件摘要及成功部署回执。
- [包内页面内容检查](tester-deployment-artifact-content.json)：独立解析实际 artifact 中的页面，逐项核对迁移文案、三个链接和公开边界。
- [公开浏览器记录](tester-deployment-browser-checks.json)：包含真实公开 URL、精确视口、元素范围、资源请求、返回导航、八个片段、摘要和逐项观察时刻。
- [公开桌面截图](tester-deployment-desktop.png)与[公开移动截图](tester-deployment-mobile.png)：测试者已查看两张实际截图。
- [分支与正式版本读回](tester-deployment-refs.json)：包含 PR 合并记录、dev 自动数据提交、main 指针和正式 test 版本。

部署层结论：通过。用户最终验收：未验证。
