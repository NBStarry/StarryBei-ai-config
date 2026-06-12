---
name: codex-review
description: 用本机 codex CLI (ChatGPT) 对当前 git 仓库的代码做独立二次审查。当用户说"让 codex 审一下"、"用 ChatGPT review"、"二次审查"、"second opinion"、"用 codex 检查"、"另一个模型看看"、"审整个项目"、"扫一遍代码"，或在 Claude 刚完成一段较大改动后用户提议复核时使用。覆盖四种范围：未提交改动 / 当前分支 vs base / 指定 commit / 整项目（无 diff）。Claude 必须原样转发 codex 的输出，不要替用户复述、过滤或评判 —— 用户要的是"另一双眼睛"的原话。
---

# Codex 代码审查

调用本机 `codex` CLI 让 ChatGPT 对当前仓库的改动做独立审查。codex 与 Claude 是不同模型，常能发现 Claude 自己忽略的问题（不同训练数据、不同 reasoning 偏好）。

## 何时使用

- 用户明确说："让 codex 审"、"用 ChatGPT review"、"二次审查"、"second opinion"、"另一个模型看看"
- Claude 刚完成一段较大改动（>100 行 / 跨多文件 / 涉及关键路径）后，**可以主动提一句**：
  > "要不要让 codex 二次审查一下？"
  让用户决定，不要替用户决定。

## 使用流程

### 1. 前置检查

- 确认 `codex` 在 PATH：`command -v codex`
- 确认当前在 git 仓库内：`git rev-parse --show-toplevel`（codex review 强依赖 git）
- 不在 git 仓库 → 告诉用户"codex review 需要 git 仓库；如要 review 任意文件可以单独 `codex exec`，本 skill 不覆盖此场景"

### 2. 询问审查范围（强制，不要默认）

每次调用前必须确认范围。给用户四个标准选项；前三档基于 git diff，第四档是无 diff 的整项目扫：

- **A. 未提交改动**：staged + unstaged + untracked → `git diff HEAD` + `git ls-files --others --exclude-standard | xargs -I{} git diff --no-index /dev/null {}`（或更简单：`git status -s` + `git diff HEAD`）
- **B. 当前分支 vs base 分支**：feature branch 完工后 → `git diff <base>...HEAD`（询问 base 名，例如 `main` / `origin/main`）
- **C. 指定 commit**：`git show <SHA>`（最常见 `HEAD`）
- **D. 整项目（无 diff）**：用户说"审整个项目"、"扫一遍代码"、"review 整个仓库"等。**先做仓库踩点**：跑 `wc -l $(find . -type f \( -name "*.py" -o -name "*.ts" -o -name "*.go" -o -name "*.rs" \) -not -path "./.git/*") | tail -3` 估总行数，跑 `find . -maxdepth 2 -type d` 列目录结构。如果总行数 > 5000 或目录里有明显的 vendored/build/test-data 子树（例如 `node_modules/`、`.venv/`、`silero-cache/`、`patches/`、`__pycache__/`、`tests/recordings/`、`tests/fixtures/`、`build/`、`dist/`），**先告诉用户你识别到的排除路径列表**让用户确认/补充，再进入步骤 3。

例外：如果上下文已经把范围说清楚（"审查刚 commit 的"→C；"看下我没提交的"→A；"扫整个项目"→D），可以直接执行不再问；其他情况一律问。

### 3. 走 `codex exec`（不要用 `codex review` 子命令）

> ⚠️ **重要约束（codex CLI 0.125 已验证）**：`codex review` 子命令的 `--commit` / `--uncommitted` / `--base` 三个范围 flag 与位置参数 `[PROMPT]` **互斥** —— 同时传会报 `error: cannot be used with [PROMPT]`。这意味着无法用 `codex review` 强制中文输出。
>
> 解决路径：用 `codex exec --sandbox read-only` 直接传带 review 指令的中文 PROMPT，让 codex 在 PROMPT 里自己跑 git 命令拿 diff。这样既保留了 review 的语义，又能控制输出语言和结构。

**A/B/C 档（基于 diff）的 PROMPT 模板**（按上一步选定的范围对应填写 `<git 范围命令>`）：

```
请扮演资深代码审查者，审查本仓库的代码改动。
第一步：跑 `<git 范围命令>` 看影响面和完整 diff。
然后用简体中文按下列结构输出 review：

1. **改动概要**（1-2 句话）
2. **Findings**（按优先级 P0/P1/P2/P3 列；每条格式：`[Px] 标题 — 文件:行号` + 一段说明 + 建议）

约束：
- 代码标识符、变量名、文件路径、函数签名一律保留原文不要翻译
- 不要写"看起来很好"、"无明显问题"这类无价值确认句；如果没 finding 就直接说"无 finding"
- 不要复述 diff 内容
- 输出仅包含上面两部分，不要前后铺垫

<可选重点>
```

**D 档（整项目，无 diff）的 PROMPT 模板**（在 `<排除路径列表>` 处填入步骤 2 与用户对齐过的 vendored/build/test-data 目录）：

```
请扮演资深代码审查者，对本仓库的核心代码做整项目级 review。

仓库布局（已为你列好）：
<这里贴步骤 2 踩点拿到的目录树和关键文件清单>

**不要 review 的路径**：<排除路径列表>

执行步骤：
1. 先 `find . -maxdepth 2 -type f -name '*.<语言后缀>' <对应 -not -path 排除>` 列出关键源文件
2. `cat` 关键模块文件（按你识别到的入口文件、核心逻辑、跨模块抽象优先），按需深入读
3. 输出 review

输出结构（用简体中文）：
1. **项目概览**：1 段（服务定位、关键依赖、运行时拓扑）
2. **架构层面 Findings**：跨模块/设计层问题，按 P0-P3
3. **模块级 Findings**：分模块（按仓库实际目录），每模块按 P0-P3
4. **正向亮点**：1-3 条本仓库做得好值得保留的设计

每条 Finding 格式：`[Px] 标题 — 文件:行号` + 一段说明（说清楚问题、潜在影响、何种条件触发）+ 一句具体建议。

约束：
- 代码标识符、变量名、文件路径、函数签名一律保留原文不要翻译
- 不要写"看起来很好"、"整体不错"这种无价值确认句；如果某个模块没 finding 就直接说"无 finding"
- 不要复述代码内容，只写问题与建议
- 优先关注：并发安全、资源泄漏（线程/socket/文件句柄/asyncio task）、错误处理、API 一致性、配置默认值的合理性、安全边界（输入校验/路径穿越/CORS/认证）、性能热点、依赖一致性（Dockerfile vs requirements）
- P 级判断：P0 上线必崩 / P1 偶发但严重 / P2 体验或维护性问题 / P3 风格或建议
- 输出仅包含上面四部分，不要前后铺垫

<可选重点>
```

**所有档**：如果用户提了重点（"重点看并发安全"、"focus on the new auth path"、"性能"），把它转成中文一句话填到末尾的 `<可选重点>` 占位符；没有就留空。

**D 档时长预期**：整项目 review 体量通常 5-15 分钟，调用 `Bash` 时 timeout 至少给 600000ms (10min)，避免被截断。如果输出较长，建议同时把 stdout 重定向到一个文件（如 `voice-service/codex-review-<date>.md`），方便用户终端外查看。

### 4. 调用并原样输出

```bash
cd "$(git rev-parse --show-toplevel)"
codex exec --sandbox read-only "<上一步拼好的中文 PROMPT>" 2>/tmp/codex_stderr.log
```

`2>/tmp/codex_stderr.log` 是为了把 codex 的 tracing/reconnect 噪音（尤其在路径含中文字符触发 0.125 的 websocket header bug 时）从 stdout 隔离开，让 review 内容干净。如果跑出来 stdout 是空的（exit code 非 0），把 stderr 文件内容贴出来给用户。

**直接把 codex 的 stdout 完整贴给用户。不要做以下任何事**：

- 用 Claude 自己的话复述 codex 的发现
- 把 codex 的多条 finding 合并去重
- 评判 codex 说得对不对、要不要采纳
- 截断长输出（codex 输出再长也原样给，让用户滚动看）

唯一例外：codex 进程退出非 0 时，把 stderr 也一起贴出，方便用户看到原始报错。

## 边界情况

| 情况 | 处理 |
|---|---|
| `codex` 不在 PATH | 告诉用户"未检测到 codex，请确认 `brew install codex` 或登录 chatgpt.com 下载" |
| 不在 git 仓库 | skip，参见步骤 1 |
| `--uncommitted` 但工作区干净（`git status --porcelain` 空）| 提前告诉用户"工作区干净，没有未提交改动可审"，不要白调用 codex |
| codex 报"未登录" | 引导用户跑 `codex login` |
| `--base main` 但 main 不存在 | 改用 `git symbolic-ref refs/remotes/origin/HEAD` 找默认分支，或直接问用户 base 名 |
| 用户想 review 任意几个文件（不在 git 里）| 不在本 skill 覆盖范围；提示可手动 `cat files \| codex exec "review these files"` |
| 路径含中文字符 | codex 0.125 的 websocket header 不支持非 ASCII，会反复 reconnect 但走 fallback 通道仍能跑通；噪音 log 走 stderr 已隔离 |

## 设计原则（理解 *为什么*）

- **"另一双眼睛"的价值在于眼睛是别人的**：用户特意找 codex 是因为想绕开 Claude 自己的盲点。Claude 复述 codex = 把 codex 的输出再过一次 Claude 的过滤器，等于没做 second opinion。
- **强制选范围是为了准确性**：审"未提交改动"和审"整个 PR"是完全不同的操作，默认错了等于浪费一次 review；用户明确选过之后下一次他可能会更主动地说清楚。
- **不加 `--dangerously-bypass-approvals-and-sandbox`**：review 是只读分析任务，没有理由放宽沙箱；codex 默认沙箱已经够用。
- **默认中文输出**：用户日常工作语言是中文，codex 默认英文输出阅读成本高、容易被 skim。强制每次调用都带中文输出指令，把"中文化"做成 skill 内置行为，调用方零负担。代码标识符/路径保留原文是为了保证可索引可粘贴。
- **D 档先踩点再排除**：整项目 review 最大风险是 codex 把上下文耗在 vendored 第三方库、build 产物、test fixture、`__pycache__` 这种"噪音目录"上，导致主代码扫不深。所以 D 档强制先用 `wc -l` + `find -maxdepth 2` 摸清规模和布局，把要排除的目录显式塞进 PROMPT。这条规则的代价是多一次仓库踩点的对齐回合，收益是 review 颗粒度真正落到核心代码上。已踩坑案例：voice-service 的 `silero-cache/` 是 vendored 第三方库 5000+ 行，不排除会把 review 注意力大量稀释。
- **D 档输出建议落盘**：终端窗口经常显示不全 D 档大几千字 review 输出，调用 D 档时建议同时把 stdout 重定向到 `<repo>/codex-review-<date>.md` 或类似文件，让用户终端外查阅。这只是建议，不强制 —— 用户明说不要落盘就不落盘。
