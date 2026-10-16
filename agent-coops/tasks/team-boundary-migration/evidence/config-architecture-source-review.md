# Config 架构源码与边界核对

日期：2026-10-16。架构角色：Codex。真实 Session ID：`01a1442a-3b97-7ef2-bfe8-51825da66b49`。本记录只保存本仓可公开的边界事实、精确路径和设计检查，不作为实际安装或用户验收证明。

## 上游与当前状态

- 本仓产品 bootstrap v1 已由总管确认。正文、manifest 和原型摘要已与 coordinator-config-product-v1.json 逐一核对。
- 产品验收为 Config A1–A8，Team A1–A12 只是追溯映射；本仓不重复定义 Team 内部运行标准。
- Team 架构 v1.3 已由总管确认。本仓只使用固定版本、已安装 loader、真实角色发布和双端接入顺序这些调用边界。Team 私有程序与运行证据不进入本仓 manifest。
- 项目现行 AGENTS、工程入口、当前任务 README 和执行记录均已读取。任务 README 中较早的 Team 架构引用需由当前任务维护者更新为最终确认版本；架构角色不改该文件。

## 已核对接口

| 本仓路径 | 当前源码事实 | 计划约束 |
| --- | --- | --- |
| install.sh | --workflow-only 在创建备份与配置前返回迁移提示；基础路径保留 Codex AGENTS 链接 | 兼容入口零宿主写入；基本安装不调用 Team 安装 |
| install.ps1 | -WorkflowOnly 在目标目录及备份初始化前返回；基础路径保留 Codex AGENTS 链接 | PowerShell 实际行为由对应环境验证，不能用字符串检查替代 |
| scripts/install-workflow.py | 只解析原 tool/home/rollback 参数并显示迁移说明 | 不删除回执，不运行旧回退或下载私有代码 |
| config/manifest.json | 已移除团队 hook/Hermes 资源，保留 codex.instructions | 移除受管项不能删除真实宿主上的既有团队文件 |
| codex/tests/test_workflow_install.py | 使用临时 HOME；检查兼容入口、基础安装、既有团队文件与来源链接、manifest | 复用现有测试；安装验证不改真实用户配置 |
| hermes/tests/test_native_runtime.py | 通过临时插件 fixture 调用实际 Hermes 分发，不调用兼容安装器 | 在真实 Hermes 虚拟环境运行；缺环境记为未验证 |
| claude/configs/CLAUDE.md | 原文仍混合模型默认、团队流程与全局 VERIFY 条件 | 保留模型语义，团队要求改为当前正本引用，不新增适配器 |
| TODO.md、VERIFY.md、docs/migrations/task-record-map.md | 当前有冻结说明及 77 条映射；映射使用修订后的来源行号和历史附件 | 采用冻结前真实快照，不用 Git HEAD 替代历史来源；飞书读回由已有迁移证据及独立测试证明 |

架构角色未重新执行安装隔离测试或飞书写入/读回。执行记录中的通过和跳过是开发阶段结果；最终测试由独立测试角色保存。

## 冻结基线

候选 Git 基线为 `819bbc4a1ad98b9fb657294806e1b06a1b269ebd`。使用 Git NUL 分隔路径读取以下集合，并逐文件比较 HEAD blob 与当前文件。40 个文件均一致：

- workflow/v0.1.0、workflow/v0.1.1、workflow/v0.1.2、workflow/v0.2.0 内全部已跟踪发行文件。
- codex/hooks/workflow-hook.py。
- hermes/workflow-plugin/__init__.py、hermes/workflow-plugin/plugin.yaml。

| workflow 版本 | workflow.py SHA-256 |
| --- | --- |
| 0.1.0 | d8f70c72133a6595612f5169f48b7486d91d28ea0ee3e1e73ada264d7fe4ac88 |
| 0.1.1 | d28292de2a65263fb8b9addd048df841ffd7c5c25e30c765d18620c09512702d |
| 0.1.2 | 04958f564240a1738b527fc1df857ebc330c367f147b0e0b1022fd8fa497e643 |
| 0.2.0 | db8ed7850aa47ecc85050cd07898d98ab9dd72a922d4947076734fa989a6241e |

这些文件只读核对，不属于本计划允许改写的 sources。hermes/workflow-plugin/README.md 属于有效归属说明，可以修改；它与冻结程序集合分开。未跟踪的 __pycache__ 不是源码或证据，不纳入候选。

## 22 个精确实现路径

| 分组 | 路径 |
| --- | --- |
| 基础安装 | install.sh；install.ps1；scripts/install-workflow.py；config/manifest.json |
| 基础与归属说明 | AGENTS.md；README.md；codex/AGENTS.md；codex/README.md；hermes/README.md；hermes/workflow-plugin/README.md；workflow/README.md |
| 本仓测试 | codex/tests/test_workflow_install.py；hermes/tests/test_native_runtime.py |
| Claude 基础规则 | claude/configs/CLAUDE.md |
| 历史迁移及入口 | TODO.md；VERIFY.md；docs/migrations/task-record-map.md；agent-coops/README.md |
| 正式接入 | agent-coops/project.json；agent-coops/run.py；STATUS.md；agent-coops/hooks/pre-commit |

共 22 个唯一文件。四个正式接入文件当前尚未创建，应在双端 loader 就绪后写入同步外候选目录。五个在办任务 README 由迁移证据覆盖。阶段正文、执行记录和 evidence 不进入实现清单。生产 site/workflow.html 仍归后续真实 Hermes Web 子目标。

## 接入前置条件

工程 worktree 与正式 Team 安装源使用同步目录外的位置。两端 loader 与旧来源兼容均通过后，再创建并集成 Projects 同步目录中的新项目入口。bootstrap 提交与正式新版门禁通过分别留回执。不得伪造真实角色身份，不覆盖既有 hook，不改其他项目的引用。

## 图示模型记录

按 free-tokens Skill 使用 phanthy-cloud/claude-opus-5-5，variant 为 medium，模型 session 为 ses_ebb8411c2ffe4f7RvcEhM9gUP5。只授权修改 config-architecture-impact.mmd，实际进程退出为 0，文件已回读；未使用 Astra 回退。

图示覆盖修改前后、基础与 Team 归属、冻结兼容、历史迁移、四个接入入口、双端 loader 时序和延后 Web 子目标。原始模型事件与提示以 config-architecture-opus-* 保存，本地原始日志不自动进入公开候选。已做基本结构核对，未安装 Mermaid 渲染器，未声称完成渲染验收。

## 未验证事项

本次只读源码及设计检查不证明：最终实现测试通过、真实双端安装完成、正式角色发布完成、实际 Git hook 接入完成、后续 Hermes Web 业务闭环完成或用户验收通过。
