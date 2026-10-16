# Config 公开团队指南迁移独立测试

## 目标与范围

本报告独立验证 `team-web-guide` 的 S1 与 A1–A4。需求正本沿用[边界迁移飞书任务](https://applink.feishu.cn/client/todo/detail?guid=9541c1a5-06aa-4762-8a76-293eaa2bf6c9)。测试者真实 Codex Session ID 为 `01a14484-7a7d-7cb0-9052-8142ac04bc3a`。runner 已将该会话绑定为本任务 tester。

唯一生产候选为 `site/workflow.html`，SHA-256 为 `00bdce81230230bff2e2444ce843273e101d56552d66a2a7a7150118f339e89d`。测试基线 HEAD 为 `4df46d8f7f5ded9504e29f0f802d77f0ec4d794c`。本报告只判定该本地候选，不代表整个边界迁移完成。

## 计划与进展

产品版本：`345522eab2fa9c1efb826076b482046ca1bd1055ee9adf991923007b17b9deac`。

计划版本：`6fac460aa8936f8b5ca3471758d0d615367270ac4119f459f102eed0a5818027`。

2026-10-16，测试者直接读取候选源码，运行独立 HTMLParser 检查，并在既有 Chrome 中观察候选页面。静态、桌面、移动与旧片段检查均核对同一源码摘要。浏览器证据来自测试者的临时静态服务与实际操作，未以开发截图或产品原型替代。

| 条件 | 结果 | 实际证据 |
| --- | --- | --- |
| A1 | pass | 标题、职责说明、权限提示与产品一致。页面只保留迁移说明和入口，无旧团队正文、脚本、嵌入、事件处理、自动跳转或状态面板。实际资源加载未出现 Team 私有源。 |
| A2 | pass | 三个原生链接的文字与 href 逐项匹配产品。返回路径为 index.html，Team 入口为已确认的 main/README.md 和仓库根地址。权限提示在两种视口均可见。 |
| A3 | pass | 真实视口为 1280×900 与 390×844。scrollWidth 分别为 1272 与 382。文字与入口无重叠、无遮挡、无横向溢出。原生 Tab 依次触达三个链接，均显示 2px 蓝色焦点线；原生 Return 成功返回 Dashboard。 |
| A4 | pass | 原文件路径保留。基本地址及 overview、architecture、five-roles、example、checks、principles、operations、limits 共八个旧片段均显示相同迁移说明。八次检查的卡片完整可见，返回 href 均为 index.html。公开部署另行验收。 |

## 阻塞与决策

本地候选没有发现需要返工的问题。产品和计划明确要求把本地实现、公开部署与用户验收分开记录，因此本次 A1–A4 可以判定通过。

公开 CI 构建产物、部署后的旧 URL、读者私有仓库授权和用户验收均未在本轮验证。本轮未进入 Team 私有正文，不对私有指南内容作结论。完整边界迁移及 Team 远端 Hermes 验收由对应任务处理。

页面沿用共享 CSS 的 Google Fonts 请求。该依赖没有改动，也没有读取 Team 私有内容。Chrome 默认请求缺失的 favicon.ico 返回 404；候选没有新增 favicon 引用，该请求未影响本轮验收条件。

测试没有修改生产页、产品、计划或开发执行记录。未运行安装器、公开数据生成、提交、推送或部署。临时视口已恢复，本任务标签已关闭，临时 loopback 服务已停止。正式报告由绑定 tester 使用 publish 生成。

## 验收与证据

- 自动检查：[静态检查与 tracked 基线](tester-static-checks.json)。基线共 151 个 tracked 文件，只有计划中的 site/workflow.html 变化，其余 150 个保持原字节。候选内容、链接、资源边界、原路径与返回文件检查全部通过。
- 实际浏览器：[独立浏览器记录](tester-browser-checks.json)。记录精确视口、元素范围、资源请求、原生键盘顺序、返回导航和八个旧片段。每项页面检查包含候选源码摘要。
- 实际截图：[桌面](tester-desktop.png)、[移动](tester-mobile.png)、[键盘焦点](tester-keyboard-focus.png)。测试者已实际查看三张截图。截图像素尺寸受显示器像素密度影响；CSS 视口尺寸以浏览器记录为准。
- 版本绑定：[测试 manifest](tester-test-manifest.json)记录产品、计划、唯一生产源码、逐项判定和独立证据摘要。
- 本地测试结论：A1–A4 通过。公开 CI 产物、线上部署与用户验收：未验证。
