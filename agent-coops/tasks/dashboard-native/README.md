# 本地 Dashboard 原生状态人工验收

[飞书原任务](https://applink.feishu.cn/client/todo/detail?guid=57062456-7138-4334-a865-d10bd34a7c1c)保存需求、负责人、状态和验收。工程任务标识为 `dashboard-native`。

## 迁移依据

用户已批准本项目在办任务采用0.2.1五角色。沿用原任务ID；保留旧入口 `docs/superpowers/plans/2026-10-08-dashboard-local-source-audit.md`、原绑定、问题记录和有效证据。原执行者交接记录由[主迁移任务](../team-boundary-migration/README.md)关联。

历史计划仅本机位置：`/Users/hanzebei/Documents/AI_Projects/StarryBei-ai-config/docs/superpowers/plans/2026-10-08-dashboard-local-source-audit.md`。SHA256：`55091f85030e1e08caf604b7f46964a6c5f6a058ae4c55a7d9cf1b1ad1add0de`。该历史草稿尚未提交，不在本次候选 worktree 中。迁移保留原文件，不把旧草稿混入新候选。

## 续接位置

从最早缺失的0.2.1产品复核与确认阶段续接。既有设计和运行结果作为输入保留，不声明旧证据覆盖新候选。

新真实 Product 已在独立 worktree 完成[产品续接复核](evidence/product-continuation.md)，来源、SHA256、真实会话及缺口见[结构化复核记录](evidence/product-continuation.json)。本记录尚未正式 publish 或 confirm；未确认上游不得进入后续阶段。全阶段沿用本任务独立目录。

当前候选仍从公共快照叠加本地数据。历史原生读取实现和测试文件保留在原 checkout，尚未进入候选。历史 CLI 与浏览器结果不证明当前候选通过，也不证明桌面全部配置覆盖。当前没有新增架构、实现或测试通过回执。

## 证据边界

人工验收保持飞书现状。历史完成勾选不代替待验收项。合同切换、自动检查、部署与用户验收分别记录；迁移不重置同一质量问题的轮次。
