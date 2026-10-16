# 项目工程入口

本项目的需求、负责人、验收要求与完成状态以项目飞书任务为正本。工程任务保存在 `tasks/<任务名>/`，同一目标复用同一入口。这里保存工程索引，不复制团队流程或第二份待办状态。

- [边界迁移工程记录](tasks/team-boundary-migration/README.md)：基础安装与 Team 独立维护边界。
- [历史 TODO](../TODO.md)与[历史 VERIFY](../VERIFY.md)：保留原条目及证据；迁移回执与逐项映射由本次迁移记录关联。读回成功前不宣称条目已迁移或已验收。
- [SuperBeiTeam 规则与安装](https://github.com/NBStarry/SuperBeiTeam)：私有仓库，需要访问权限。

本目录不自动安装门禁。已配置项目仍使用其固定合同；新的安装与版本切换需要相应授权。

## 迁移后的工程入口

飞书保留当前状态；各入口只关联原文、旧证据和续接位置。

- [Dashboard 项目预加载与会话实际上下文](tasks/dashboard-context/README.md)。
- [以本机状态核对并更新配置模板](tasks/config-baseline/README.md)。
- [Dashboard 全页面样式统一人工验收](tasks/dashboard-style/README.md)。
- [Dashboard 按具体钩子脚本展示人工验收](tasks/dashboard-hooks/README.md)。
- [本地 Dashboard 原生状态人工验收](tasks/dashboard-native/README.md)。
