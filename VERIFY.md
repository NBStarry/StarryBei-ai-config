# Verification Checklist / 验证清单

本文件只记录无法由自动测试可靠判断、必须由用户观察真实 UI 或运行时行为的验收项。
文件结构、语法、JSON、生成数据和安全排除规则由 GitHub Actions 自动验证。

## How It Works / 工作流程

1. PR 和 `dev` / `main` push 先通过 GitHub Actions 自动检查
2. 只有需要观察 UI、工具加载或真实机器行为的改动才添加到本清单
3. 改动推送到 `dev` 后，用户按自然语言步骤验收并填写实际效果
4. 所有相关人工验收项通过后，才可合并到 `main`

## Status Legend / 状态说明

- `[ ]` — 待验证：已推送到 `dev`，等待用户观察真实行为
- `[x]` — 已验证：用户确认改动效果符合预期
- `[-]` — 已废弃：改动不符合预期，需要修改或移除

---

## Current Manual Verification / 当前人工验收

<!--
格式：
- [ ] **改动简述** (commit: abc1234, date: YYYY-MM-DD)
  - 验证方法：描述需要观察的 UI 或运行时行为，不放语法/文件检查命令
  - 预期效果：描述预期结果
  - 实际效果：（验证后填写）
-->

### Dashboard CI/CD and branch viewer

- [ ] **Dashboard 分支查看 + repo-only CI/CD** (commit: pending, date: 2026-07-12)
  - 验证方法：等待 `dev` Actions 完成 Pages 预览部署后，打开 GitHub Pages Dashboard；在顶栏切换 `main` / `dev`，观察 URL 是否出现可分享的 `?branch=<name>`，侧栏数据是否随分支更新；观察 `dev` 是否显示 GitHub 编辑入口、其他分支是否只读，错误分支是否保留原页面。
  - 预期效果：分支切换、URL、数据和只读状态一致，页面布局与交互无异常。
  - 实际效果：（验证后填写）

- [ ] **本地完整 Dashboard** (commit: pending, date: 2026-07-12)
  - 验证方法：在 Windows PowerShell 启动 `pwsh -File .\scripts\start-local-dashboard.ps1`，观察浏览器是否打开 `local (this machine)`；查看 Skills、Configs、Inventory 和 Dashboard 统计，再切换到 `main` / `dev` 比较数据。
  - 预期效果：本地页展示当前机器实际安装的 Claude/Codex skills 与插件，Inventory 显示 installed / missing / drifted，Configs 能看到脱敏后的本地结构；认证文件和真实 token 不出现，页面只读；切换 GitHub 分支后恢复对应在线 desired state。
  - 实际效果：（验证后填写）

- [ ] **Inventory 内容展开 + GitHub 原生编辑认证** (commit: pending, date: 2026-07-12)
  - 验证方法：在线 Dashboard 切换到 `dev` 并打开 Inventory，展开 Settings、Instructions、Codex config、Prompt 或 Skill 的 `View content`；点击 `GitHub Edit`，观察是否直接进入对应文件的 GitHub 编辑页。退出 GitHub 登录后再次点击，应由 GitHub 自己要求登录，Dashboard 不应出现 token 输入框。
  - 预期效果：受管资源展示 Git 已跟踪的公开来源内容；本地版相同区域只显示脱敏内容；编辑认证完全由 github.com 处理，Dashboard 不读取或保存 GitHub token。
  - 实际效果：（验证后填写）

- [ ] **PowerShell 配置迁移闭环** (commit: pending, date: 2026-07-12)
  - 验证方法：先运行 `pwsh -File .\scripts\config.ps1 plan` 观察真实配置差异；确认备份范围后运行 `apply` 和 `verify`，重启 Claude/Codex 观察配置与 skills 是否正常；最后可用 `rollback` 观察最近一次迁移是否能恢复。
  - 预期效果：plan 不修改本机；apply 只处理 missing / drifted 项并留下事务与备份；verify 与 Dashboard Inventory 状态一致；rollback 能恢复迁移前状态。
  - 实际效果：（验证后填写）

### Codex prompt adapters

- [ ] **checkpoint slash prompt 适配器** (commit: pending, date: 2026-07-08)
  - 验证方法：在 Windows PowerShell 执行仓库根目录的 `pwsh -File .\install.ps1`，重启 Codex 或新开 Codex chat，观察 slash 菜单是否出现 `/prompts:checkpoint`；分别在有和没有 checkpoint 工作流的项目中试用。
  - 预期效果：Codex slash 菜单出现 `/prompts:checkpoint` 本地入口；它只作为适配器触发当前 repo 的 checkpoint skill / `scripts/checkpoint.sh`。裸 `/checkpoint` 仍不是 Codex 官方支持的自定义命令形式。
  - 实际效果：（验证后填写）

### Runtime integration

- [ ] **web-access skill 兼容 Codex 路径解析** (commit: pending, date: 2026-07-07)
  - 验证方法：在 Codex 会话中输入“用 web-access 查一下 https://example.com 的标题”，观察它是否找到 Windows 上实际安装的 skill、连接 Chrome 并返回页面标题；若 Chrome 未授权，只按提示开启 remote debugging 后重试。
  - 预期效果：Codex 不再尝试访问不存在的 `~/.claude/skills/web-access`；路径解析到 `~/.codex/skills/web-access` 或 `~/.agents/skills/web-access`；普通沙箱能明确提示本地 TCP 被挡；允许本地端口访问后显示 `chrome: ok (port 9222)` 和 `proxy: ready`，联网任务可继续使用 CDP API。
  - 实际效果：（验证后填写）

- [ ] **整理根 README 并纳入 web-access npm 依赖元数据** (commit: pending, date: 2026-07-01)
  - 验证方法：阅读 GitHub 上的根 `README.md`，观察快速开始、目录结构、Claude/Codex/hzb-skills/Dashboard 说明是否清晰准确；在 Windows 安装后确认生产 Claude 配置仍正常加载。
  - 预期效果：README 对 Windows 用户可直接执行，文档与实际安装行为一致。
  - 实际效果：（验证后填写）

### Karpathy guidelines skill

- [ ] **karpathy-guidelines skill 在 Dashboard 可见** (commit: pending, date: 2026-06-16)
  - 验证方法：最新改动推送并由 CI 刷新 `dev` 数据后，在 Dashboard 切换到 `dev`，搜索 `karpathy-guidelines` 并打开详情。
  - 预期效果：Dashboard skills 列表出现 karpathy-guidelines；内容包含 Think Before Coding、Simplicity First、Surgical Changes、Goal-Driven Execution 四条原则
  - 实际效果：推送前检查时没出现，待 `dev` 更新后复验

### 插件/skill 全量盘点 (recommended-plugins.json)

- [x] **recommended-plugins.json 改为多 marketplace 全量清单** (date: 2026-06-15)
  - 验证方法：在 Dashboard 观察 marketplace 和插件清单是否完整、无 `pua` 相关项。
  - 预期效果：含 longxiabei Mac 上盘点到的源（新增 `telegram` 等；`pua`/`pua-skills` 应按用户偏好被移除、不出现），每插件标注所属 marketplace 与携带 skill；Dashboard 不报错
  - 实际效果：正确更新

### Windows 适配 (install.ps1 / settings.windows.json / statusline.ps1)

- [ ] **statusline.ps1：jq-free PowerShell 状态栏** (date: 2026-06-14)
  - 验证方法：Windows 上启动 Claude Code，观察状态栏在普通路径、长路径和中文会话名下的实际显示。
  - 预期效果：渲染 `◆会话 · 路径 · 模型·1M · 分支 · ctx%`，UTF-8 字形（◆ ·）正常、ANSI 颜色生效、路径过长省略为 `首/次/…/末2/末1`、ctx% 按 50/80 阈值变色；无 jq 依赖
  - 额外验证：**中文会话名**（如 `配置测试Claude`）不乱码——stdin 按 UTF-8 字节读取（`OpenStandardInput`），规避 PS 5.1 用 OEM 代码页(GBK)解码管道导致的乱码；脚本本身以 UTF-8 BOM 保存，规避 PS 5.1 把无 BOM .ps1 当 GBK 读
  - 实际效果：（验证后填写）

- [ ] **settings.windows.json：Windows 专属配置** (date: 2026-06-14)
  - 验证方法：`install.ps1` symlink 后，`~/.claude/settings.json` 指向本文件；启动 Claude Code 检查 statusline 生效、代理 env 生效、插件按 enabledPlugins 加载
  - 预期效果：statusLine 用 PowerShell 命令、`HTTP(S)_PROXY` 写在 env（Windows 无 zshrc 继承）、其余 plugins/model/effortLevel 与 macOS settings.json 一致
  - 实际效果：（验证后填写）

- [ ] **install.ps1：Windows 安装器** (date: 2026-06-14)
  - 验证方法：在 Windows PowerShell 执行 `pwsh -File .\install.ps1`，观察 Claude/Codex 重启后配置、statusline 和 `/prompts:checkpoint` 是否实际可用；同时确认已有本地配置未被无提示覆盖。
  - 预期效果：文件用 symlink（需开发者模式/管理员）、目录用 junction（免提权、跨盘）、已有文件先备份到 `~/.ai-config-backup-*`；缺开发者模式时给出明确提示并继续创建 junction
  - 实际效果：（验证后填写）

### 多工具配置仓库改造 (my-claude-code → StarryBei-ai-config)

- [x] **仓库改名 + 引用更新** (commit: 7306c74, date: 2026-06-11)
  - 验证方法：访问 `https://github.com/NBStarry/StarryBei-ai-config`；旧 URL `.../my-claude-code` 应 301 重定向；打开新 Pages `https://nbstarry.github.io/StarryBei-ai-config/`，Dashboard 编辑功能（走 GitHub API REPO 名）能拉取并保存一次文件
  - 预期效果：远程仓库名、本地 remote、editor.js 的 REPO、README/CLAUDE.md 的 clone URL 全部为新名；Dashboard CRUD 正常
  - 实际效果：✅ 已验证。旧 URL 正确 301 跳转到新仓库名

- [x] **目录重构为 claude/ + codex/ 分层** (commit: 670d420, date: 2026-06-11)
  - 验证方法：本地重跑 `bash scripts/generate-site-data.sh`，检查 `site/data.json` 各 tab（skills/hooks/configs/scripts/commands）数量均不为 0；`bash -n` 所有 .sh 通过
  - 预期效果：目录迁移后 Dashboard 数据扫描路径正确，无空 tab
  - 实际效果：✅ 已验证。data.json：skills=93 hooks=1 configs=4 scripts=1 commands=1 plugins=10，全部非 0；所有 .sh 通过 bash -n

- [x] **install.sh symlink 模式 + settings.json 原子写存活** (commit: pending, date: 2026-06-11)
  - 验证方法：`bash install.sh` 后 `ls -la` 确认 `~/.claude/{settings.json,CLAUDE.md,statusline.sh}` 均为指向仓库的 symlink；新开 Claude 会话执行 `/model` 切换→退出→`[ -L ~/.claude/settings.json ]` 仍为 symlink
  - 预期效果：symlink 不被原子写打断（若打断则回退 copy 模式）；插件与 statusline 正常
  - 实际效果：✅ 已验证。所有 symlink 就位；`/model` 切换后 settings.json 仍为 symlink（Claude Code 用普通写穿透 symlink，不用原子 rename，symlink 模式安全）

- [x] **敏感信息未泄漏到公开仓库** (commit: ef615d4, date: 2026-06-11)
  - 验证方法：`git log -p` 全历史 grep `sshpass -p|pw=|sk-|ghp_|ss://` 无真实值命中；本仓库的 settings.local.json / legacy settings.glm.json 在 .gitignore 内、未被跟踪；hzb 私有 overlay 由独立仓库管理
  - 预期效果：仓库内只有脱敏 .example 模板，无任何真实密钥
  - 实际效果：✅ 已验证。本次 5 个 commit + 全仓库 --all 历史 grep（机器人密码/relay 凭证/SakuraFrp pw/GLM token/OpenRouter key/飞书 ID/邮箱）零命中；这些密钥从未进入任何 git 历史；5 个含密真身经 git check-ignore 确认未跟踪；push 到 GitHub 未被 secret scanning 拦截

- [-] **本地配置同步：sync-configs.sh + Dashboard Configs 增强** (commit: pending, date: 2026-04-12)
  - 原因：sync-configs.sh 的复制+双向同步机制已被 install.sh 的 symlink 模式取代，脚本移入 deprecated/（仓库改造为多工具配置库时）

- [-] **Telegram bridge /compact 命令** (commit: pending, date: 2026-04-12)
  - 原因：Telegram 通知方案已弃用，脚本归档在 deprecated/（仓库改造为多工具配置库时移除）

- [ ] **Dashboard 全局搜索：Ctrl+K 快捷键 + 下拉结果 + 分类导航** (commit: pending, date: 2026-03-30)
  - 验证方法：打开 Dashboard，按 Ctrl+K 聚焦搜索框，输入关键词确认下拉结果出现，点击结果导航到对应页面，按 Escape 关闭
  - 预期效果：搜索支持 skills/hooks/configs/scripts，结果按类型分组，最多 10 条，点击可导航
  - 实际效果：（验证后填写）

- [ ] **Memory 页面 Gist 集成 + export-memory.sh** (commit: pending, date: 2026-03-30)
  - 验证方法：
    1. 打开 Memory 页面，确认显示 auth gate（锁图标 + 密码输入框 + Unlock 按钮）
    2. 不输入 token 点击 Unlock，确认提示 "Please enter a token"
    3. 输入 token 但 MEMORY_GIST_ID 为空，点击 Unlock，确认提示 "MEMORY_GIST_ID not configured"
    4. 配置实际 Gist 后观察导出结果是否能被页面读取
  - 预期效果：auth gate 正常显示，错误提示准确，真实 Gist 导出和读取成功
  - 实际效果：（验证后填写）

- [-] **telegram-bridge /list 进程检测 + 目标终端显示 + 动态选项标签** (commit: pending, date: 2026-02-10)
  - 原因：Telegram 通知方案已弃用，脚本归档在 deprecated/（仓库改造为多工具配置库时移除）

---

## Verified / 已验证项目

<!-- 已验证通过并合并到 main 的改动记录 -->

- [x] **CLAUDE.md 质量优化：Quick Start + 去重 + 补全架构文档** (commit: abf0ecc, date: 2026-02-10)
  - 验证方法：确认 Quick Start、statusline、deprecated 章节存在，行为规则无重复
  - 实际效果：验证通过

- [x] **Insights 优化事项落实：CLAUDE.md 规则 + merge-verified skill + bash-syntax-check hook** (commit: f4bf932, date: 2026-02-10)
  - 验证方法：确认新规则生效，skill 和 hook 文件就位
  - 实际效果：验证通过

- [x] **Telegram 通知完整内容 + /full + 权限选项修复** (commit: aadafba, date: 2026-02-10)
  - 验证方法：/full 获取完整代码修改、权限选项 2 导航、/pane 完整滚动历史
  - 实际效果：全部功能正常

- [x] **telegram-bridge.sh 多终端支持** (commit: 42bfb6a, date: 2026-02-09)
  - 验证方法：/list 列出终端、/connect 切换、自动失效检测
  - 实际效果：session 切换和自动检测正常

- [x] **Telegram 双向通信系统** (commit: 4c8ce1d, date: 2026-02-09)
  - 验证方法：Telegram 收发通知、bridge 消息注入、特殊命令
  - 实际效果：长轮询稳定，功能完整

- [x] **configs/CLAUDE.md 添加 Agent Teams 模型规则** (commit: c98b850, date: 2026-02-09)
  - 验证方法：Agent Team 创建时遵循模型选择规则
  - 实际效果：验证通过

- [x] **CLAUDE.md 重写 + 启用 Agent Teams 配置** (commit: 17ed37f, date: 2026-02-09)
  - 验证方法：Claude Code 正确读取架构说明和 Git 工作流规则
  - 实际效果：验证通过

- [x] **QQ 消息桥接 (qq-bridge.sh)** (commit: 6beec01+5198337, date: 2026-02-06)
  - 前提：websocat 已安装，tmux 中运行 Claude Code，LLOneBot 在线
  - 验证方法：手机 QQ 发送消息，检查是否注入到 Claude Code 终端
  - 预期效果：发送 "1" → Claude Code 选择授权；发送文本 → 作为输入；`/status` → 返回状态
  - 实际效果：`/status` 返回状态正常，文本消息成功注入终端

- [x] **statusline.sh 自定义状态栏** (commit: 3ad032f, date: 2026-02-06)
  - 验证方法：重启 Claude Code，检查底部状态栏
  - 预期效果：显示 user@host:dir + 模型名 + Git 分支 + 上下文用量
  - 实际效果：已确认正常工作（安装 jq 后）

- [x] **notification.json macOS 通知 hooks** (commit: 9db8d12, date: 2026-02-06)
  - 验证方法：重启 Claude Code，执行操作触发权限请求和任务完成
  - 预期效果：收到系统通知横幅 + 提示音
  - 实际效果：已确认工作正常

- [x] **QQ 消息通知 (notify-qq.sh)** (commit: aedcfff, date: 2026-02-06)
  - 前提：安装 LiteLoaderQQNT + LLOneBot，桌面 QQ 登录机器人号
  - 验证方法：手机 QQ 收到来自机器人号的通知消息
  - 预期效果：收到格式化的通知（含项目名、工具详情、授权选项）
  - 实际效果：已确认手机推送正常

- [x] **notify-qq.sh 格式优化** (commit: 99adfce, date: 2026-02-06)
  - 验证方法：等待 hook 触发，检查 QQ 通知格式
  - 预期效果：`[任务完成] 项目名` 单行标题，空行分隔回复和上下文，无分割线，无 emoji
  - 实际效果：已确认格式正确

- [x] **configs/CLAUDE.md 全局指令** (commit: 448ec7c, date: 2026-02-06)
  - 验证方法：在任意项目中确认 Claude Code 遵守 commit 规则
  - 预期效果：代码与相关文档始终在同一 commit 中提交
  - 实际效果：已确认生效

- [x] **QQ 通知显示上下文百分比 (notify-qq.sh)** (commit: a90cd82, date: 2026-02-07)
  - 验证方法：等待 hook 触发，检查 QQ 通知第一行是否包含 `[ctx:XX%]`
  - 预期效果：`[任务完成] my-project [ctx:34%]`
  - 实际效果：上下文百分比显示正常，符合预期

- [x] **远程访问文档 (README.md)** (commit: e5deddc, date: 2026-02-09)
  - 验证方法：检查 README.md 中 Remote Access 章节内容是否准确
  - 预期效果：包含 SSH + Tailscale + tmux 配置步骤、架构图、常见问题
  - 实际效果：文档内容准确，符合预期

---

## Deprecated / 已废弃项目

- [-] **通知改用 display alert 持久对话框** (date: 2026-02-06)
  - 原因：改用 QQ 通知方案，macOS 系统通知不再需要

- [-] **notify-qq.sh Agent Team 来源显示** (commit: 04771c7, date: 2026-02-09)
  - 原因：QQ 方案已废弃，已迁移到 deprecated/

- [-] **qq-bridge.sh TCP 状态 watchdog** (commit: 882cb8e, date: 2026-02-07)
  - 原因：QQ 方案已废弃，已迁移到 deprecated/

- [-] **qq-bridge.sh v2 全面改进** (commit: 218d27b, date: 2026-02-09)
  - 原因：QQ 方案已废弃，已迁移到 deprecated/

- [-] **qq-bridge.sh 自动启动 QQ + 启动通知** (commit: 05ef7de, date: 2026-02-09)
  - 原因：QQ 方案已废弃，已迁移到 deprecated/
