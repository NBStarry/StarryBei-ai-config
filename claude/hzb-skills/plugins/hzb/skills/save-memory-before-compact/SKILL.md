---
name: save-memory-before-compact
description: 把本次会话的跨会话稳定事实写入 memory 文件, 避免上下文压缩冲掉关键知识。当用户说"保存重要信息我要 /compact"、"准备压缩上下文"、"compact 前 save memory"、"重要事实存进记忆"、"sync memory"、"压缩前归档关键信息", 或主动说"保存"/"归档"/"sync"+"memory"/"记忆"+上下文相关词时使用。也在完成一个有意义的里程碑(库选型决策 / 踩坑根因 / 部署事实变化 / 用户偏好)后主动调用, 把稳定事实即时落盘。注意: 无法靠 PreCompact hook 自动触发(机制不支持 additionalContext 注入), 只能手动触发或里程碑自觉。
---

# Save Memory Before Compact

把本次会话产生的**稳定事实**写入 `~/.claude/projects/<proj-hash>/memory/` 跨会话保留, 避免上下文压缩时丢失。手动触发, 或在里程碑后自觉调用。

## 为什么需要这个 skill

底层逻辑: `/compact` 把 N 轮对话压缩成 1 段摘要, **细节会丢**。但有些事实是跨会话稳定的 (库选型决策、踩坑教训、新部署事实), 跟当前任务无关但下次会话需要。这些事实不写进 memory, 压缩后就再也找不回。

## 触发方式与一个重要限制

**不能靠 PreCompact hook 自动触发**: 试过 PreCompact hook 注入 additionalContext 提醒 Claude 调本 skill, 但 harness 的 PreCompact 事件**不支持 `hookSpecificOutput.additionalContext`** (只有 PreToolUse / UserPromptSubmit / PostToolUse / PostToolBatch 支持), hook 输出会被判非法直接报错。更本质的: `/compact` 是 `hook → 立即压缩`, 中间**没有 Claude 推理回合**, 任何 hook 都无法让 Claude 在压缩前主动干活。所以这条自动化路径机制上死掉了 (2026-05-27 验证)。

实际触发方式:

1. **用户手动触发** (主路径): "保存重要信息我要 /compact" / "准备压缩" / "把这次会话关键事实存 memory" / "sync memory"
2. **Claude 里程碑自觉** (推荐习惯): 完成一个有意义的里程碑后 (确定了库选型 / 定位了踩坑根因 / 部署事实发生变化 / get 到用户偏好), **当场**就把这条稳定事实落 memory, 不要攒到压缩前 —— 攒到压缩前就晚了, 因为没有 hook 兜底。

## 工作流程 (4 步)

### Step 1: 摸清现有 memory 状态

```bash
ls ~/.claude/projects/<proj-hash>/memory/        # <proj-hash> = 当前工作目录的 Claude project hash
```

或直接读已加载的 `MEMORY.md` 索引看现有条目, 避免写重复 memory。

### Step 2: 盘点本次会话稳定事实

**只写跨会话有价值的事实**, 按全局 CLAUDE.md memory 4 类:

- **user**: 用户角色 / 偏好 / 知识背景变化
- **feedback**: 用户纠正过的做法 / 验证过的有效路径 (带 **Why** + **How to apply**)
- **project**: 项目里发生了什么 / 谁在做什么 / 为什么 / 截止日期 (相对日期转绝对)
- **reference**: 外部资源位置 (Linear / Slack 频道 / 飞书文档 URL)

**反例 - 不写**:
- ❌ Commit hash 列表 (`git log` 看)
- ❌ 文件路径 / 代码片段 (`grep` / `Read` 看)
- ❌ 当前任务进度 / TodoList 状态 (ephemeral)
- ❌ Debug 临时假设 (验证过的根因+解法才存)
- ❌ 简单"看到 X 就改 Y" 这种代码常识 (LLM 自己能推)

### Step 3: 写 / 更新 memory 文件

**先查 existing, 再决定 update or create new**:

- 已有相关 memory → `Edit` 追加段或更新过时事实 (附"更新时间" + 何时旧 fact 不再适用)
- 新主题 → `Write` 新文件, 命名 `<type>_<short-slug>.md`, 含 frontmatter:

```markdown
---
name: short-kebab-case-slug
description: 一行总结 (跨会话识别这个 memory 的依据, 必须 specific)
metadata:
  type: user|feedback|project|reference
  originSessionId: (当前 session id, 可选)
---

(内容. feedback/project 类: 先事实, 然后 **Why:** + **How to apply:** 两行. 用 [[other-memory-slug]] 链接相关.)
```

### Step 4: 同步 MEMORY.md 索引

`MEMORY.md` 是索引文件不是 memory 本身, 每条 ≤150 字符:

```markdown
- [Short Title](file.md) — 一行 hook 解释何时回来看
```

新写的 memory 必须加进 MEMORY.md, 否则下次会话看不到入口。

## 输出格式 (告诉用户)

3 行内汇报:

```
✓ 写入 N 个 memory:
  - <file1> (新增/更新): 一句话内容
  - ...
- MEMORY.md 加 N 行索引

跳过 (按规则不写 memory):
  - <类型>: 一句话原因 (e.g., "commit hash 列表 → git log 自查更准")
```

## 边界情况

| 场景 | 处理 |
|---|---|
| 会话非常短 / 没产生稳定事实 | 输出 "本次会话无跨会话稳定事实需保存" 然后 return; 不强行写 memory |
| 用户在 hook 触发后说"不用保存" | 跳过, 直接让 /compact 继续 |
| memory 目录不存在 | 创建 (mkdir -p) 后继续 |
| 现有 memory 跟新事实**冲突** | 优先信新事实 (用户最新交互), 更新旧 memory + 加"过时事实" 备注 |

## 设计哲学

- **存"事实"不存"任务"**: 任务在 TodoList / commit message 里; memory 存"这件事的根因 + 解法 + 适用边界"
- **跨会话 > 当前会话**: 当前任务进度让 /compact 摘要去, memory 专门管下次会话也用得上的东西
- **不重复**: existing memory 能 cover 就更新, 不滥建新文件
- **链接 > 嵌套**: 用 `[[slug]]` 链接相关 memory, 不把所有事实塞一个文件
