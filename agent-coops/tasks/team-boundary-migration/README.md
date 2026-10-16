# 基础配置与团队边界迁移

[飞书迁移主任务](https://applink.feishu.cn/client/todo/detail?guid=9541c1a5-06aa-4762-8a76-293eaa2bf6c9)同时关联两项目清单，保留同一需求ID。

本入口只保存 StarryBei-ai-config 的工程范围。业务需求、产品设计和技术计划使用同一迁移目标，不新增平行需求。

## 设计来源

本仓使用已确认的 Config bootstrap v1：[产品设计](产品设计.md)、[技术计划](计划.md)、[产品确认回执](evidence/coordinator-config-product-v1.json)和[架构确认回执](evidence/coordinator-config-architecture-v1.json)。产品正文 SHA-256 为 `874a3d62c1385fe90918dc8520623260288b2d03d7206cd88d96510a55b26fc6`；计划正文 SHA-256 为 `4104377a73e1e131ef23fbde056958a6284855281afc39ff9b5b4f5eb51bca4e`。bootstrap 确认不代表已正式发布或接入新版门禁。

本仓计划承接 [SuperBeiTeam 主产品 v1 与架构 v1.3](https://github.com/NBStarry/SuperBeiTeam/tree/main/agent-coops/tasks/team-boundary-migration)，需要私有仓库访问权限。该路径供发布后追溯，不表示远端已发布。团队正本及其确认版本以本仓计划中的来源记录为准。

## 本仓范围

- 基础安装继续链接 Codex 基础原则；移除团队自动安装和 manifest 团队受管项。
- 旧团队安装参数仅提示私有 Team 入口，不写配置或下载代码。
- 基础原则及有效文档只维护基础职责，团队内容指向 Team。保留 Claude 的五条模型选择语义；合并验收遵守目标项目当前有效正本。
- 保留旧 workflow 发行文件及 hook/plugin 程序字节，已有消费者不卸载、不迁移。
- 本仓 TODO、VERIFY 的映射与冻结由迁移总管处理；最终 Web 指南由后续真实 Hermes 任务交付。

## 工程证据

[本仓执行记录](执行记录.md)区分自动检查、实际运行和用户验收。当前入口不构成新门禁已安装、部署完成、工程确认或用户验收回执。
