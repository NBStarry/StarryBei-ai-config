# Hermes 开发规范接入

`workflow-plugin/` 使用 Hermes 原生插件接口。它读取配置仓 `codex/AGENTS.md` 中的共用原则，并复用 `codex/hooks/workflow-hook.py` 和项目固定的 `workflow/v0.1.0/workflow.py`。不复制规范程序，不修改 Hermes 源码，不替换 Profile 的身份或团队派发规则。

## 安装和回退

从配置仓根目录运行：

```bash
~/.hermes/hermes-agent/venv/bin/python -B scripts/install-workflow.py --tool hermes
```

如果虚拟环境在其他位置，使用该 Hermes 环境中的 Python。安装器依赖 Hermes 已有的 PyYAML。它链接 `~/.hermes/plugins/starrybei-workflow`，并向 `config.yaml` 的 `plugins.enabled` 添加插件名。其他配置字段保持原值；YAML 注释和排版会规范化，原文件完整保存在本机备份中。

独立成员需逐个使用 `--home ~/.hermes/profiles/<profile>`。安装器不自动发现或修改其他 Profile。`bash install.sh --workflow-only` 只检测并处理当前 Codex 和 Hermes 主入口；使用 `HERMES_HOME` 时处理该 Hermes 配置目录。

安装后新开 CLI 会话，或在没有运行中任务时重启网关。回退使用同一 Python 执行 `scripts/install-workflow.py --rollback <安装时打印的receipt.json>`，然后重新加载进程。目标被后来操作修改时，回退拒绝覆盖。不要把含私有配置的备份提交到仓库。

## 检查如何执行

| Hermes 入口 | 行为 |
| --- | --- |
| `pre_llm_call` | 每个会话首次进入项目时，注入共用原则及项目接入状态 |
| `tool_execution` 中间件 | 使用 Hermes 任务目录解析器，转换 `write_file`、`patch`、`terminal` 的参数，在实际调用前后运行共用检查 |
| `pre_verify` | 检查本会话涉及项目的待查结果；失败时要求继续处理，不能宣称通过 |
| `on_session_end` | 再核对待查结果；成功后释放进程内会话状态 |

中间件只在存在 `agent-coops/project.json` 的项目启用门禁。未接入项目保留原流程，不自动创建目录或任务。配置仓路径、版本或程序 SHA-256 不匹配时拒绝已接入项目的操作。

同一会话的受检工具调用串行执行，避免 v0.1.0 的单份待查记录被并发覆盖。不同会话保持独立。插件返回的检查错误会阻止实际调用；它不会将检查异常抛给 Hermes 后静默放行。写入后的结果不一致时保留文件并报告，不自动回退其他操作者的修改。

Hermes 任务仍使用真实 `session_id` 绑定规划或执行角色。已有 SuperBeiTeam 的 Kanban 派发和独立复核保留。飞书仍是需求与用户验收正本；插件不会完成飞书任务。

## 验证

本地隔离测试：

```bash
python3 -B -m unittest discover -s codex/tests -v
python3 -B -m unittest discover -s workflow/v0.1.0/tests -v
```

目标机器的原生运行时测试：

```bash
HERMES_SOURCE="$HOME/.hermes/hermes-agent" \
  ~/.hermes/hermes-agent/venv/bin/python -B hermes/tests/test_native_runtime.py -v
```

原生测试使用临时 Hermes 配置和测试项目，运行真实插件发现、上下文注入及工具分发，不调用模型。真实模型会话需另验：合法写入成功、违规根文件返回 `PATH_DENIED` 且未创建，并核对事件记录。当前部署与验收事实见[本次执行记录](../docs/plans/2026-10-13-codex-root-principles.md)。

## 限制

当前适配已按 longxiabei 的 Hermes 原生接口实现，仅支持 `local` 终端后端。其他后端路径不一定属于宿主文件系统，插件明确报告不支持。升级 Hermes 后重跑原生测试，尤其核对任务目录解析和中间件接口。

原生移动语法会转换成共用程序可检查的文本补丁。v0.1.0 按文本末尾换行计算结果；非空且没有末尾换行的文件会在移动前明确拒绝，避免生成错误的通过证据。二进制移动不在此文本适配范围。

任意 shell、解释器和 MCP 写入不能完整事前还原；已接入项目继续保留 Git 候选提交检查。`pre_verify` 由 Hermes 的验证流程触发，不是每次回复的全局完成认证。检查与用户验收分别记录。
