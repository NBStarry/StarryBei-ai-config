# Config 公开团队指南入口迁移

本工程属于[边界迁移任务](../team-boundary-migration/README.md)的公开入口子目标。需求与用户验收正本沿用[飞书任务](https://applink.feishu.cn/client/todo/detail?guid=9541c1a5-06aa-4762-8a76-293eaa2bf6c9)。本目录保存工程证据，不创建第二份业务待办。

## 工程产物

- [产品设计](产品设计.md)定义迁移文案、三个原生入口和 A1–A4。
- [技术计划](计划.md)限定唯一生产文件 `site/workflow.html`。
- [执行记录](执行记录.md)记录候选实现与开发检查。
- [独立测试](evidence/测试验收.md)记录同一候选的自动检查、实际浏览器和原生键盘结果。
- [设计确认回执](evidence/coordinator-design-confirmations.json)保存产品与架构确认及双渠道通知状态。
- [最终工程确认](evidence/coordinator-final-confirmation.json)记录本地完成结论、三次确认及六项通知状态。

## 验证边界

本地候选已通过独立 A1–A4 检查。公开 CI 产物、部署后的旧 URL 与用户验收由主迁移任务继续记录。Team 私有指南由 Team 工程维护；本公开页不读取私有正文。
