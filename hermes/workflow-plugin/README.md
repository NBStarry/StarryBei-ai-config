# Hermes 开发规范插件

`starrybei-workflow` 通过 Hermes 原生插件接口加载共用原则，并在工具调用前后执行项目固定版本的规范检查。插件仅对已接入项目启用门禁。

使用配置仓的 `scripts/install-workflow.py --tool hermes` 安装。安装器建立插件链接，并合并 `plugins.enabled`；仅建立链接不会启用插件。安装后重新加载 Hermes 进程。

安装、回退、验证和已知限制见 [Hermes 接入说明](../README.md)。
