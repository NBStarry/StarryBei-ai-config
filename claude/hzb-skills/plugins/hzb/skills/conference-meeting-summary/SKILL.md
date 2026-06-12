---
name: conference-meeting-summary
description: 把"会议原始素材文件夹"（钉钉闪记转写链接 .txt + 现场录音 .wav + iPhone 拍的 .HEIC slide 照片）批量沉淀成飞书云文档，含完整转写存档 + slide 嵌入 + 与闪记自带 AI Summary 的命名实体纠错对比。Use when user mentions VALSE / CVPR / NeurIPS / ICML 等学术会议素材整理、钉钉闪记 / shanji.dingtalk.com 链接、会议转写整理、HEIC 照片批量处理成文档、会场 slide 总结、用闪记 + 飞书做会议纪要。Trigger on phrases like "整理会议录音""会议总结""把这场 workshop 写成飞书文档""帮我把闪记转成文档""转写文本 + 照片 → 文档"。即使用户只说"整理这场会"，只要场景是"链接 + 录音 + 照片"的会议素材，也应该用本 skill；不要试图自己从头摸索。
---

# Conference Meeting Summary（会议素材 → 飞书文档）

## 适用场景

输入是「一个会议素材根目录」，里面长这样（VALSE2026 命名约定，但通用化适用）：

```
D-VLASE2026-武汉-2026.05-原始资料/
├── A1-Workshop-VLA-具身智能安全-1.txt        # 钉钉闪记 URL
├── A1-Workshop-VLA-具身智能安全-1-...wav     # 现场录音（不用，校验用）
├── A1-Workshop-VLA-具身智能安全/             # iPhone 拍的 HEIC slide 照片
│   ├── IMG_8351.HEIC
│   └── ...
├── A2-Workshop-VLA-具身智能强化学习系统演进.txt
├── A2-Workshop-VLA-具身智能强化学习系统演进-...wav
├── A2-Workshop-VLA-具身智能强化学习系统演进/
└── ... 更多会议
```

**输出**：每场会议一个飞书云文档，含：
- 会议元信息（讲者、时间、时长、原始链接）
- 一句话总览 + 演进时间线表 + 章节正文
- 26 张（量级不定）slide 嵌入到对应章节，自然阅读顺序
- 与钉钉闪记自动 AI Summary 的差异对比表（**命名实体纠错是核心价值**）
- **关键技术索引**（客观陈述：论文/arXiv/GitHub URL/数据集/产品名/对比工作；**不要**写"用户视角"/"公司视角"/"P0/P1/P2 跟进"——Claude 没掌握用户岗位与公司战略，强行下判断只会传播错误）

## 底层逻辑（为什么这套 SOP 有效）

1. **钉钉闪记的 AI Summary 几乎不可信**：业内技术名词、英文缩写、产品名、合作方名字几乎全是语音识别错误（实测 A2 一场 17+ 处错）。"儿童"=RLinf、"看尔苗"=π_RL、"微量"=NVIDIA、"AMB"=AMD。直接抄 AI Summary 等于把错误传播下去。
2. **slide 是 ground truth**：会场 slide 上的英文、人名、URL、数字是讲者亲自审过的。**用 slide 校正 AI Summary，再用 transcript 补足讲者口头展开的内容**，才是高质量纪要。
3. **slide 嵌入文档不是装饰**：它是「这一段总结对应当时是哪一页 PPT」的可追溯锚点。后续读者要核实某条结论时能直接看到原图。
4. **存档转写原文**：transcript 是会议的"原始数据"，AI Summary 只是衍生品。txt 落盘后续可以重新检索、重新生成。

## 视角铁律（最高优先级）

**Claude 没有掌握用户的岗位、公司战略、团队上下文、资源约束**。整理任何文档时——

- ❌ **禁写**："<YOUR_NAME>视角" / "4Paradigm 视角" / "个人 take-aways" / "我们应该做 X" / P0/P1/P2 优先级判断 / "这件事重要" 等带价值判断的话
- ✅ **改写为客观索引**：用"**关键技术索引**"或"**可索引信息**"作为章节名；只罗列论文 / arXiv ID / GitHub URL / 数据集 / 产品 / 与其他工作的对比；让用户自己判断重要性

这一条违反一次就是失败交付。

## 完整 SOP（按顺序执行，**不要跳步**）

### 步骤 0 · 盘库存 + 规划

`ls` 根目录，按命名前缀（A1/A2/B1...）列出会议清单。识别四种异常：
- **多段录音同会议**（如 A1-1 / A1-2）：合并成同一场处理
- **多 URL 同会议**（一个 .txt 里有多行 URL，如 A3）：分别抓取、拼接
- **无转写**（.txt 内容是 `没有转写`，12 字节左右）：走 slide-only 分支或暂停问用户
- **空照片目录**（如 A8）：纯文字总结，无嵌图

把会议清单告诉用户，让用户确认从哪场开始 / 是否串行 / 是否并行。**不要默默全跑**。

### 步骤 1 · 钉钉闪记抓取（CDP）

调用 `web-access` skill 启 CDP Proxy。`scripts/extract_shanji.js` 包含抓取代码——
**核心是 React fiber 走树拿 `paragraphs` 数据**（不靠虚拟滚动）：

```bash
# 启 CDP
bash ~/.claude/skills/web-access/scripts/check-deps.sh

# 打开钉钉闪记 URL
TARGET=$(curl -s "http://localhost:3456/new?url=<钉钉闪记 URL>" | jq -r .targetId)
sleep 3  # 等页面渲染

# 抽数据
curl -s -X POST "http://localhost:3456/eval?target=$TARGET" \
  --data-binary @~/.claude/skills/conference-meeting-summary/scripts/extract_shanji.js
```

返回的 JSON 含 `transcript`（带时间戳和说话人）+ `aiSummary` + 元数据。

**为什么用 fiber 走树而不是滚动**：钉钉闪记用 react-window 虚拟化，DOM 里只渲染可见的 7-10 段，滚动只会 unmount 旧的 mount 新的，innerText 永远抓不全。但 React 组件 props 上挂了完整的 `paragraphs` 数组（126 段全在内存），从 fiber 树往上找含 `paragraphs` 属性的节点就能一次拿全。

**多段 / 多 URL 处理**：每个 URL 独立跑，最后把 `paragraphs` 数组按时间戳拼接（多段录音注意时间偏移，第二段时间戳要加上第一段总时长）。

### 步骤 2 · 照片处理

**HEIC → JPG 批量转换**（macOS `sips`）：

```bash
mkdir -p _extracted/<会议代号>-photos
for h in <会议照片目录>/*.HEIC; do
  name=$(basename "$h" .HEIC)
  sips -s format jpeg -Z 1600 "$h" --out "_extracted/<会议代号>-photos/${name}.jpg" >/dev/null 2>&1
done
```

`-Z 1600` 长边压到 1600px，平衡可读性和上传体积。

**逐张读取识别**：用 `Read` tool 把 jpg 当 image 读，提取每张 slide 的标题 + 关键内容 + 引用文献 / URL。**这是 skill 最依赖模型能力的一步**——耐心读完所有照片，整理成 slide → 章节映射表（"IMG_8375 = M2Flow 框架图 → 章节 4.2"）。

### 步骤 3 · 落盘 transcript + AI Summary

写两个 txt 到 `_extracted/`：
- `<会议代号>-转写原文.txt`：含元数据 header + `[mm:ss] Speaker: 内容` 格式
- `<会议代号>-闪记纪要.txt`：原始 AI Summary 原样保留（待 diff 用）

### 步骤 4 · 起草飞书文档 markdown

**统一文档结构**（用户在 A2 验收过这个范式，不要随意改动）：

```
# <会议代号> · <题目>
> 元信息（讲者 / 时间 / 时长 / 原始闪记链接）
---
## 一句话总览
## 演进时间线（或议题脉络 / 关键里程碑）— 表格形式
---
## 1. <第一章>     # 一律 h2，序号开头
## 2. <第二章>
### 2.1 <子章节>   # h3，可选
...
---
## N. 与钉钉闪记 AI Summary 的差异（查漏补缺）
## N+1. 个人 take-aways（<用户身份> 视角）
```

**核心要求**：
- 章节标题用 `## <序号>. <名字>` 格式，序号 + 唯一文字便于后面 `--selection-with-ellipsis` 锚定
- AI Summary 纠错表用 markdown table，三列：`AI Summary 写法 | 正确名称 | 纠错来源`
- 时间线 / 数据 / 对比都用 table
- 论文 / arXiv ID / GitHub URL 显式带上（slide 上有就写）

参考完整范例：`references/sample-a2-doc.md`

### 步骤 5 · 飞书文档创建

**严格用 jushen-team profile**（CLAUDE.md 项目规则）：

```bash
lark-cli docs +create --api-version v2 \
  --profile jushen-team \
  --doc-format markdown \
  --content "$(cat <doc.md>)"
```

返回 `document.url`，保存——后续插图 + 授权都用它。

### 步骤 6 · 嵌入 slide 照片（反向序策略）

**这一步用户最容易踩坑**，必须按本 SOP 来：

底层逻辑：`docs +media-insert --selection-with-ellipsis "X"` 把图片插到匹配文本 X 的 block 之**后**。多张图共用同一锚点时，**后插入的会出现在更上面**（每次都顶到锚点正下方，把已存在的图片推下去）。

**因此规则**：

| 场景 | 策略 |
|---|---|
| 单章节 1 张图 | 直接 `--selection-with-ellipsis "<章节标题唯一片段>"` |
| 单章节 N 张图 | **按时间反序**逐张插入。最后想显示的图（第 N 张）**最先插入**；想显示在最上面的图（第 1 张）**最后插入** |

**坑**：caption 是 image block 的属性，不进 markdown 视图，**不能用前一张 caption 做下一张的锚点**——只能用章节标题、章节内 plain text、`--before <后继 plain text>` 三选一。

**强制要求**：**先 cd 到照片目录再调用**——`--file` 必须是相对路径（lark-cli 安全检查），绝对路径会被拒。

`scripts/insert_slides.sh` 提供模板。

### 步骤 7 · 授权用户访问

**bot 创建的文档默认只有 bot 可见，用户看不到**。必须显式授权：

```bash
lark-cli drive permission.members create \
  --profile jushen-team --as bot \
  --params '{"token":"<docx_token>","type":"docx","need_notification":"false"}' \
  --data '{"member_id":"<union_id>","member_type":"unionid","perm":"full_access","perm_type":"container","type":"user"}' \
  --yes
```

**用户的 union_id 获取方式**（仅当本目录没缓存时）：
```bash
lark-cli contact +get-user --user-id-type union_id --profile <YOUR_APP_ID>
```

union_id 因人而异（形如 `on_xxx`，仅在自己的 tenant 内有效）。每个用户必须用 lark-cli 现场查询自己的 union_id。

### 步骤 8 · 自检 + 汇报

抓 doc 验证：

```bash
lark-cli docs +fetch --api-version v2 --profile jushen-team --as bot \
  --doc "<URL>" --detail with-ids --doc-format xml > /tmp/verify.json
python3 <<'EOF'
import json, re
raw = open("/tmp/verify.json").read()
data = json.loads(raw[raw.find("{"):])
content = data["data"]["document"]["content"]
imgs = re.findall(r'<img[^>]*name="([^"]+)"', content)
print(f"Total img blocks: {len(imgs)}")
for i, n in enumerate(imgs): print(f"  {i+1}: {n}")
EOF
```

确认嵌图数量 = 照片数量。如果错位，依次找出错位章节修正。

**回报用户**：URL + 嵌图数 + AI Summary 纠正了多少处 + 等用户验收。

## 已知陷阱（踩过的坑）

| 陷阱 | 触发条件 | 解法 |
|---|---|---|
| `--api-version v2` flag 在 `media-insert` 不存在 | 全局沿用习惯加上去 | 只有 `+create` / `+fetch` / `+update` 才需要 `--api-version v2` |
| `--yes` flag 在 `media-insert` 也不存在 | 全局沿用习惯 | **不要加 `--yes`**。该指令不是 high-risk，不需要它；加了报 unknown flag 全失败 |
| `--file` 必须相对路径 | 给绝对路径 | `cd` 到照片目录再调用 |
| `permission.member:create` scope 缺失 | jushen-team app 没申请过 | console 申请 scope（URL 在 error 提示里） |
| `media:upload` scope 缺失 | 同上 | 同上 |
| 用 caption 做下一张图的锚点失败 | 误以为 caption 在 markdown 视图里 | 改用反向序策略，所有图锚到章节标题 |
| AI Summary 直接抄进文档 | 偷懒 | **永远先用 slide 校正命名实体**——这是用户感知到的最大价值 |
| 钉钉闪记页面 innerText 不全 | DOM 虚拟化 | React fiber 走树拿 `paragraphs` 数组 |
| HEIC 文件 Read tool 读不了 | 直接 read .HEIC | `sips` 转 jpeg 后再 read |
| CDP `/close` 端点是 GET 不是 DELETE | 误以为 RESTful 风格 | `curl -s "http://localhost:3456/close?target=$ID"`（GET） |
| 闪记把会场旁人对话误识别为会议主体 | ASR 漏剔噪 | transcript 抓到与主题完全不相关的姓名 / 单位时（如"打印材料/食堂"等场外内容），标注剔除并写入 AI Summary 纠错表 |
| 讲者姓名识别错 / 缺失 | 闪记 ASR + slide 无署名 | 元信息里标注"闪记识别为 XXX，待核实"，不要装作权威 |
| transcript 70%+ 是会场杂音 / 杂谈 | 会场嘈杂 + 闪记单麦近场录音 + 会议中断 | 切换到 **"slide 为主、transcript 为辅"** 模式：文档主体内容 100% 从 slide 重建，transcript 仅用于补充讲者口头展开的细节；AI Summary 纠错表里明确"应整段剔除"杂音段落 |
| 圆桌会议多 Speaker 闪记错归属 | 多嘉宾，闪记把不同人合并到同一 Speaker | 用 Speaker N 编号 + 内容上下文（自我介绍/闭幕致谢/口头风格）三角定位真实身份；身份未确认的明确标 `待核实` |
| 多段录音合并时间戳对不上 | 第 2 段 startTime 从 0 重新开始 | 第 2 段所有 startTime / endTime 加上第 1 段 `endTime`（=偏移量，单位 ms）；txt 落盘用合并后时间轴 |
| 短录音段 `scrollables[0]` 不是 transcript 容器 | 段数少 / AI Summary 容器比 transcript 高 | extract_shanji.js v2 已升级：遍历所有 scrollable + body fiber DFS 兜底；返回 `foundIdx` 调试用 |
| 照片目录混入非 slide 图（如 `37c4bb7e...JPG` 会场远景） | iPhone 自动同步把会场场景照也放进来 | 转 JPG 后先 Read 浏览一遍，剔除非 slide 图（背景人物 / 横幅 / 设备特写）再嵌入 |

## 关键 references

| 文件 | 用途 |
|---|---|
| `scripts/extract_shanji.js` | 钉钉闪记 CDP eval 脚本：fiber 走树 + transcript/AI Summary 双抽 |
| `scripts/heic_to_jpg.sh` | HEIC 批量转 JPEG 模板 |
| `scripts/insert_slides.sh` | 反向序嵌图模板（含 helper function） |
| `references/feishu-permissions.md` | jushen-team app 缺/有的 scope 清单 + console 申请 URL |
| `references/sample-a2-doc.md` | 完整 A2 文档作为范式参考（用户验收过的） |

## 调用其他 skill 的边界

| 阶段 | 用哪个 skill |
|---|---|
| CDP 浏览器操作（打开钉钉闪记） | `web-access` |
| 飞书文档 create / fetch / update / media-insert | `lark-doc` |
| 用户 open_id / union_id 查询 | `lark-contact` |
| 文档权限 / 删除 | `lark-drive` |

**不要在本 skill 里重复造轮子**——这些都是上游 skill 的职责，本 skill 只是把它们编排在一起。
