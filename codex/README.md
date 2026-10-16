# Codex CLI 配置

本目录管理 OpenAI Codex CLI（`~/.codex/`）的可分享配置。

## 文件说明

| 文件 | 用途 | 是否纳入版本管理 |
|------|------|------------------|
| `config.toml.example` | Codex 主配置模板（模型、TUI、项目信任） | ✅ 模板入库 |
| `prompts/*.md` | Codex 本地 slash-menu prompt 适配器 | ✅ 模板入库 |
| `~/.codex/config.toml` | 实际配置 | ❌ 仅本地（Codex 会自动改写，含本机路径） |
| `~/.codex/prompts/*.md` | `install.ps1` / `install.sh` 链接出的本地 prompt | ❌ 仅本地入口 |
| `~/.codex/auth.json` | OAuth token | ❌ 绝不入库（`codex login` 生成） |

## Skills

Codex 与 Claude Code 共用的自建 skills 已迁移到独立仓库
[`NBStarry/hzb-skills`](https://github.com/NBStarry/hzb-skills)。本仓库的安装器管理
Codex 配置模板、prompt adapter、全局开发原则、规范 hook 和 `config/skill-plugins.json` 中声明的公开 plugin。
本机私有 skill 链接由各自的安装流程负责。

## Slash prompt 适配器

Codex 不会把 `.agents/skills/<name>` 自动注册成 `/<name>` slash command。
官方仍支持但已标注 deprecated 的本地 Custom Prompts 可以把
`~/.codex/prompts/*.md` 暴露到 slash 菜单，调用形式是
`/prompts:<name>`。

本仓只把这类文件当作薄适配器使用：`codex/prompts/checkpoint.md`
会被安装器链接到 `~/.codex/prompts/checkpoint.md`，提供
`/prompts:checkpoint` 入口；真正的 checkpoint 规则仍以当前项目里的
`checkpoint` skill、`scripts/checkpoint.sh` 和 `AGENTS.md` 为准。
新增或修改 prompt 后，需要重启 Codex 或新开 Codex chat 才会加载。

## 首次安装

```powershell
# 从仓库根目录运行，统一链接 Claude/Codex skills 和 prompts
pwsh -File .\install.ps1

# 若 config.toml 尚不存在，复制模板后填写项目信任路径
Copy-Item .\codex\config.toml.example $HOME\.codex\config.toml
codex login
```

macOS/Linux 使用仓库根目录的 `bash install.sh`。

## VS Code 终端标题

`config.toml.example` 的 `tui.terminal_title` 会让 Codex 通过 OSC 标题序列输出
运行状态和会话名。VS Code 还需要把终端 Tab 标题来源切换为 `${sequence}`；仓库
中的 [vscode/settings.json](../vscode/settings.json) 提供了可合并到用户设置的最小片段。

不要用该片段覆盖现有的 VS Code `settings.json`。合并设置并重启 Codex 后，空闲时
Tab 显示会话名，运行时显示类似 `⠋ session-name` 的活动状态。

## 为什么 config.toml 不 symlink

Codex 运行时会自动改写 `config.toml`（追加 project trust level、记录 model
migration 与 availability 提示等）。若把它 symlink 到仓库文件，这些自动写入会
污染 git 工作区，且会把本机特定路径写进公开仓库。因此 config.toml 只提供模板，
由用户复制后本地维护。

## 本机根原则与规范检查

在采用0.2.0的项目中，新任务使用总管、产品、架构、开发、独立测试五角色。总管通过宿主原生子 Agent 分派，用 `delegate` 记录角色，用 `confirm` 确认产品、架构及最终结果。三个确认节点都同步到当前会话和飞书机器人私聊，用户无需回复。测试失败后自动返工，同一问题第三轮仍失败时请求用户决策。通知失败如实记录，不撤销已确认结果。旧任务及已有绑定保留原流程，详见[五角色规范](../workflow/v0.2.0/README.md)。

`AGENTS.md` 是 Codex 全局原则正本，本机 `~/.codex/AGENTS.md` 链接到此文件。项目规则继续决定目录、任务格式和验证命令。规范入口 `hooks/workflow-hook.py` 链接到 `~/.codex/hooks/workflow-hook.py`。两项链接登记在 `config/manifest.json`。`python3 -B scripts/install-workflow.py --tool codex` 安装链接并合并四项 hook；两个总安装器也调用此入口。重复安装不重复注册，回退方式见根 README。

安装器在 `~/.codex/hooks.json` 中保留原有项，为 `SessionStart`、`PreToolUse`、`PostToolUse`、`Stop` 分别合并 command hook。macOS/Linux 默认目录使用以下定义；自定义目录和 Windows 使用安装时的 Python 及入口绝对路径。不要覆盖整个配置：

```json
{"type":"command","command":"python3 -B \"$HOME/.codex/hooks/workflow-hook.py\"","timeout":10,"statusMessage":"Codex 规范检查"}
```

- 会话开始：提示根原则和当前项目检查范围。
- 已有 `agent-coops/project.json`：核对版本、规范路径及 SHA-256，再调用本配置仓内对应的 `workflow.py`。不会执行项目自带的任意 `run.py`。
- 写入前：复用项目目录、计划正文、任务归属及证据检查；失败时拒绝调用。
- 写入后与结束：核对已记录的本次调用结果，不扫描其他任务的全部脏文件，不自动回退文件。
- 未接入项目：保留原有 hook，会话开始明确提示未接入共用门禁，不自动建立目录或飞书任务。

参考了具身智能团队的四阶段 hook 和按仓库、按调用检查方式。TokenDeck 的重复 Codex 项目 hook 已移除，Git pre-commit 及 Claude 配置保留。其他已接入项目切换到全局入口时，也须检查重复注册。

新 hook 需要在 Codex `/hooks` 中审阅并信任精确定义。全局与项目 hook 会同时加载，不存在项目配置自动覆盖全局配置的规则。参见 [Codex 官方 hook 文档](https://learn.chatgpt.com/docs/hooks)。新会话用于验证全局原则和 hook 加载；文件已写入不代表当前运行中会话已刷新。

限制：原则中的沟通风格和验收真实性仍需审查。任意 shell/MCP 写入不保证事前解析；已接入项目仍须保留候选提交检查。没有 Git 的项目按最近的 `agent-coops/project.json` 定位。当前部署面向 macOS，未验 Windows。

检查命令：`python3 -B -m unittest discover -s codex/tests -v`。任务记录见 [Codex 本机原则与规范检查](../docs/plans/2026-10-13-codex-root-principles.md)。

面向使用者的规则解释、允许与拒绝示例，参见[开发规范 Web 指南](../site/workflow.html)。
