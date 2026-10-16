# Global Rules

## Git Commit Rules
- Code changes and related documentation updates must be in the same commit — never split them into separate commits
- 开始项目工作时，读取项目 `AGENTS.md` 与当前任务记录，确认该项目当前有效的验收正本。
- 合并到 `main` 前，完成该正本要求的全部相关用户验收。旧项目继续遵守其原有效流程；不要把已冻结的历史 `VERIFY.md` 作为所有项目的强制验收清单。

## Editing Rules
- Before editing any file, always re-read its current content with a fresh `Read` — never edit based on assumed or stale content
- Verify file existence on disk before claiming files exist

## Language
- Default to Chinese when replying to the user, unless the user explicitly asks for another language

## Shell Scripts & Debugging
- When fixing shell scripts, always test runtime behavior with a real invocation — do not rely solely on reading the code
- For tmux operations: use `capture-pane -S -` for full scrollback
- Build and test regex patterns incrementally in Bash one-liners before embedding in scripts
- All `.sh` files must pass `bash -n` syntax check before committing

## Approach-First Workflow
- For shell script fixes, regex extraction, and non-trivial debugging: propose the approach (with specific commands/flags) before executing
- Identify root cause first, then propose fix — do not jump directly into implementation

## 模型选择

- 子 Agent 调用 `Agent` 工具时，必须显式传入 `model` 参数，值为 `opus` 或 `sonnet`。不得省略该参数并继承主循环模型。
- 主代理始终使用 `model: "opus"`。
- 常规成员默认使用 `model: "sonnet"`。
- 复杂任务使用 `model: "opus"`，包括架构、多文件重构和深度调试。
- 成员不得使用 `haiku`。

## 团队规则引用

团队权限、任务拆分和阶段 checkpoint 遵守目标项目当前有效合同。规范维护入口为 [SuperBeiTeam 私有仓库](https://github.com/NBStarry/SuperBeiTeam)，需要仓库访问权限。本文件只维护基础规则，不复制团队流程正文。

## 飞书 / lark-cli Rules
- **文档归属 = 创建身份**：`lark-cli docs +create` 默认用 **bot（应用）身份**创建，文档 owner 就是该应用（如「HZB 飞书 CLI」），不是用户本人。后果：user 身份删不掉、移动不了，飞书 UI 会提示"向 XX 应用申请删除/无权限"。
- **删/改 bot 创建的文档必须用 `--as bot`**：报 `1062501 operate node no permission`（API）或 UI"申请删除"弹窗时，先判断 owner 是不是 bot——是就换 `--as bot` 操作，一次成功，不要在 user 身份上反复撞或误判成租户/密级策略。
- **想让文档归属用户**：创建时显式用 user 身份（需先 `auth login` 拿对应 scope）；否则默认进 bot 名下。
- **Drive 文档迁入 Wiki 常被拦**：`wiki +move` 报 131006 / 只能"提交申请"时，绕法 = `wiki +node-create` 直接在知识库节点下新建原生 wiki 文档再灌内容（`docs +update --command append`），不走 move。
- 删除是高风险写操作，`drive +delete` 需 `--yes`；删前先确认 token 是目标文档（别删错 wiki 正式版）。
