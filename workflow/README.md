# workflow 冻结兼容说明

团队合同、程序、宿主适配和团队安装的唯一维护入口是 [SuperBeiTeam 私有仓库](https://github.com/NBStarry/SuperBeiTeam)，需要访问权限。新接入请使用 Team 的安装说明。

本仓 `v0.1.0/`、`v0.1.1/`、`v0.1.2/` 和 `v0.2.0/` 保留为冻结发行快照。版本目录中的程序、模板、文档和测试不再修改。原路径、程序字节和 SHA-256 保持不变，既有消费者可继续使用；目录内的旧安装说明仅作为历史记录。

`codex/hooks/workflow-hook.py` 与 `hermes/workflow-plugin/` 的程序也保留冻结兼容。基础安装不再启用这些团队适配器，也不卸载已安装适配器。旧 `--workflow-only`、`-WorkflowOnly` 和 `scripts/install-workflow.py` 只给迁移提示，不拉取私有代码。

项目迁移须有明确授权。本次不修改其他项目的版本引用、角色绑定和运行状态。工程范围与检查见 [边界迁移工程入口](../agent-coops/tasks/team-boundary-migration/README.md)。
