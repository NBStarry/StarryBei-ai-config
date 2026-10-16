# 以本机状态核对并更新配置模板

[飞书原任务](https://applink.feishu.cn/client/todo/detail?guid=90c57f97-119d-4f0c-b914-b2f9f2e991cb)保存需求、负责人、状态和验收。工程任务标识为 `config-baseline`。

## 迁移依据

用户已批准本项目在办任务采用0.2.1五角色。沿用原任务ID；保留旧入口 `docs/superpowers/plans/2026-10-08-dashboard-local-source-audit.md`、原绑定、问题记录和有效证据。原执行者交接记录由[主迁移任务](../team-boundary-migration/README.md)关联。

历史文件位置：韩泽北的MacBook Pro 上的原 checkout 本机路径：`/Users/hanzebei/Documents/AI_Projects/StarryBei-ai-config/docs/superpowers/plans/2026-10-08-dashboard-local-source-audit.md`。文件 SHA256：`55091f85030e1e08caf604b7f46964a6c5f6a058ae4c55a7d9cf1b1ad1add0de`。该历史草稿尚未提交，不在本次候选 worktree 中；读取历史时使用这个入口。迁移保留原文件，不把旧草稿混入新候选。

## 续接位置

从最早缺失的0.2.1产品复核与确认阶段续接。既有设计和运行结果作为输入保留，不声明旧证据覆盖新候选。

2026-10-16，新 Product 已在独立 worktree 完成实际输入复核，见[产品续接输入复核](evidence/product-continuation.md)和[来源摘要与检查记录](evidence/product-continuation.json)。本次没有执行正式 `publish` 或 `confirm`，没有新增设计确认或测试通过回执。

当前候选与原 checkout 的模板、插件清单和本地 Dashboard 实现不同。原 checkout 保留历史未提交改动；当前候选插件清单仍包含 Claude 5 项和 Codex 2 项，不能沿用历史“仅 Codex hzb”的安装预览结论。

最早缺失阶段仍是当前候选的正式 Product 发布与确认。后续先明确历史改动归属，再安排候选实施与验收。新会话按实际角色绑定；未确认上游不得进入后续阶段。本任务全阶段使用当前独立 worktree；不得与其他任务共用候选目录。

## 证据边界

人工验收保持飞书现状。历史完成勾选不代替待验收项。合同切换、自动检查、部署与用户验收分别记录；迁移不重置同一质量问题的轮次。
