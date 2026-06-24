# Global Rules

## Git Commit Rules
- Code changes and related documentation updates must be in the same commit — never split them into separate commits

## Editing Rules
- Before editing any file, always re-read its current content with a fresh `Read` — never edit based on assumed or stale content

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

## Agent Teams Rules
- **Subagents (Agent tool) must always pass an explicit `model` parameter** (opus or sonnet) — never omit it, since omitting inherits the main-loop model, which may be an unintended tier
- Team Lead: always use `model: "opus"`
- Teammates: default to `model: "sonnet"`, use `model: "opus"` for complex tasks (architecture, multi-file refactoring, deep debugging)
- Never use haiku for teammates
- Verify file existence on disk before claiming files exist
- Never merge to `main` without all VERIFY.md items marked `[x]`
- Confirm teammate permissions before assigning tasks
- Break complex multi-agent setups into smaller validated steps
- Provide checkpoint summaries after each major step

## 飞书 / lark-cli Rules
- **文档归属 = 创建身份**：`lark-cli docs +create` 默认用 **bot（应用）身份**创建，文档 owner 就是该应用（如「HZB 飞书 CLI」），不是用户本人。后果：user 身份删不掉、移动不了，飞书 UI 会提示"向 XX 应用申请删除/无权限"。
- **删/改 bot 创建的文档必须用 `--as bot`**：报 `1062501 operate node no permission`（API）或 UI"申请删除"弹窗时，先判断 owner 是不是 bot——是就换 `--as bot` 操作，一次成功，不要在 user 身份上反复撞或误判成租户/密级策略。
- **想让文档归属用户**：创建时显式用 user 身份（需先 `auth login` 拿对应 scope）；否则默认进 bot 名下。
- **Drive 文档迁入 Wiki 常被拦**：`wiki +move` 报 131006 / 只能"提交申请"时，绕法 = `wiki +node-create` 直接在知识库节点下新建原生 wiki 文档再灌内容（`docs +update --command append`），不走 move。
- 删除是高风险写操作，`drive +delete` 需 `--yes`；删前先确认 token 是目标文档（别删错 wiki 正式版）。
