# Config 公开团队指南入口源码核对

核对日期：2026-10-16。真实 architect 会话：`01a1442a-3b97-7ef2-bfe8-51825da66b49`。工作分支为 `SuperBei/team-web-guide`，基线 HEAD 为 `4df46d8f7f5ded9504e29f0f802d77f0ec4d794c`。本次核对没有修改生产文件。

## 当前页面

`site/workflow.html` 为 25,572 字节的旧团队长篇正文，包含目录、八个正文片段、主题按钮和一份脚本引用。页面引用 `css/style.css?v=20261008`、`css/workflow.css`、`js/workflow-doc.js`。

`site/css/style.css` 已提供 reset、颜色与字体变量、默认主题、`:focus-visible`。其既有 Google 字体导入保持原状；本次不新增网络资源。该文件的 body 使用 flex，而 `site/css/workflow.css` 的 `body.workflow-doc` 已改为 block，可直接保留文档基础样式。

`workflow.css` 的旧 `doc-layout` 为目录与正文双栏，不适合单卡入口。新页直接使用专属主区域类和少量页内布局，不使用旧双栏结构，不修改共享文件。原主题脚本依赖 `#doc-theme`，因此删除按钮时同时删除本页的脚本引用；脚本文件本体保持不变。

## 基线摘要

| 文件 | SHA-256 |
| --- | --- |
| site/workflow.html | `26b0c987fd94a09334c37bec647fdea6cbdb20839dea877c5363d1646b611e90` |
| site/css/style.css | `a3854f856558252d6901441d9db8e1ce6c004781f1ce72a81ccda2c58f263eb1` |
| site/css/workflow.css | `62df4674e5fe4fb2c83077ce2abed738b5d72f41c34dfa1c9f412568070b323b` |
| site/js/workflow-doc.js | `123b04ec684e62decd2b972b4e29520109328af3500701c601dc84c0b58b8974` |
| site/index.html | `0e9c25f3bea72bc4ea2152bfe593eb1744da394f76de8a219a20109b98670a2b` |
| site/js/app.js | `9f4c234586658597cc58948ae7f4ef9f47b6aa61d161900765e0655e003af5ed` |
| site/js/editor.js | `f535a048640d8a8fb1e292a6053b43aea4c7f925cca727f8753eb06cc69b8606` |
| site/data.json | `2df32214d965b29930fa973570d0dfdb77289e5e0172d625d9d1a69c9fe24f2d` |

架构阶段没有改变这些文件。开发候选只允许改变第一项。

## 上游与接口

产品正式版本为 `345522eab2fa9c1efb826076b482046ca1bd1055ee9adf991923007b17b9deac`，当前状态已确认。产品正文 SHA 为 `c36a58eb42ca99b7f5e21d69ab3b66a9a366a526d37c07ee897d3f0499f80643`；manifest SHA 为 `8f742ecf49e63ca0caea506d6ab226acf8c18fc2f822b6e9fefd874708a88601`；原型 SHA 为 `7fdabdb791b947f0f6de29477939d0c7866f16209fd4e121feba8da645921d51`。

产品元数据证据已经确认 Team 仓库和 main/README.md 存在。本架构没有读取私有正文。三个生产链接完全采用产品目标。未知旧片段不改变 HTTP 文档路径，浏览器仍加载 workflow.html；实际可见性留给候选浏览器验证。

## 架构资产与证据边界

影响图只描述公开入口、共享样式复用、单页变更和验证边界。图由 `free-tokens` 实际调用 `phanthy-cloud/claude-opus-5-5`、`medium` 制作。紧凑模型回执保存于 `architecture-model-receipt.json`；完整输入、事件、stderr 和会话导出放入已忽略的 `model-local/`。

本次源码阅读与资产检查不等于生产实现、浏览器或部署验收。计划正式发布与总管确认分别由真实角色执行。没有修改产品或执行实现。
