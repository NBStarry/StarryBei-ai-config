---
name: okf
description: 创建、转换、审查和维护 Open Knowledge Format (OKF) v0.1 知识包。用于用户明确提到 OKF、Open Knowledge Format、LLM wiki、agent-readable knowledge bundle、metadata as code，或要求把数据目录、指标定义、API、runbook、playbook、schema 和长期知识整理成可移植、可版本控制、供人和 agent 共读的 Markdown + YAML frontmatter 语料时。不要为普通单篇 Markdown 文档自动套用 OKF。
---

# Open Knowledge Format

把分散的元数据、上下文和经过整理的知识沉淀为可移植的 OKF bundle。遵循“格式而非平台”：产物必须能被普通编辑器、Git、搜索工具和不同 agent 直接读写，不依赖专有服务、SDK 或运行时。

开始创建或审查前，读取 [references/okf-v0.1.md](references/okf-v0.1.md)。该文件记录官方 v0.1 的严格合规边界、保留文件和字段规则。

## 工作流程

### 1. 确定范围与证据

- 明确 bundle 描述的系统、数据域或业务范围，以及目标读者和消费者。
- 收集权威来源：schema、代码、API 规范、runbook、指标定义、数据目录或用户提供的材料。
- 区分来源事实、合理推断和待确认内容。不要为了填满模板编造字段、关系、SLA 或业务语义。
- 确认输出位置。除非用户明确要求，不要默认把知识包写进当前仓库。

### 2. 设计目录与概念边界

- 把 bundle 设计为 Markdown 目录树；一个概念对应一个非保留 `.md` 文件。
- 让文件相对路径成为稳定的 concept ID，例如 `tables/orders.md` 对应 `tables/orders`。
- 按领域组织目录，不强制预设 taxonomy。使用能被当前组织理解的分组和 `type`。
- 仅把 `index.md` 用作渐进披露目录，把 `log.md` 用作时间倒序更新记录；不要把它们当普通概念文件。

### 3. 编写概念文档

- 每个概念文件使用 UTF-8 Markdown，并在文件开头放置可解析的 YAML frontmatter。
- 始终填写非空 `type`。优先补充 `title`、`description`、`resource`、`tags` 和 `timestamp`，但没有可靠信息时不要伪造可选字段。
- 允许生产者添加领域字段；审查或往返修改时保留不认识的 frontmatter key。
- 正文优先使用标题、列表、表格和 fenced code block。按需要使用 `# Schema`、`# Examples`、`# Citations` 等约定标题，不制造固定正文模板。

### 4. 建立链接与来源

- 使用普通 Markdown 链接表达概念关系，并在周围文字中说明关系语义，例如 joins-with、depends-on 或 references。
- 优先使用 bundle-relative 绝对路径，例如 `[customers](/tables/customers.md)`；同目录短链接可使用相对路径。
- 对来自外部材料的事实，在文末 `# Citations` 中列出可追溯来源。
- 发现断链时报告并尽量修复；消费或审查时不要仅因断链拒绝整个 bundle。

### 5. 维护渐进披露与历史

- 在大型目录添加 `index.md`，按分组列出概念和子目录，并带简短 description。
- 需要记录知识演进时添加 `log.md`；日期标题使用 `YYYY-MM-DD`，最新日期在前。
- 避免复制概念正文到 index。index 只帮助人和 agent 先发现、再按需加载。

### 6. 验证并交付

先执行严格合规检查：

1. 每个非 `index.md` / `log.md` 的 `.md` 文件都有可解析的 YAML frontmatter。
2. 每个概念都有非空 `type`。
3. `index.md` 和 `log.md` 在存在时遵循各自结构。

再执行质量检查：

- concept ID 和目录是否稳定、易理解。
- 关键事实是否有权威来源或明确标注待确认。
- 重复内容是否可合并为链接。
- index 是否支持渐进披露，交叉链接是否足以表达图关系。
- 未知 type、扩展字段、缺失可选字段和暂时断链是否被宽容处理。

交付时报告 bundle 根目录、新增/更新的概念、引用来源、断链或待确认项，以及严格合规结果。

## 边界

- 不把 OKF 当作固定 ontology、schema registry、数据库或知识服务。
- 不用 OKF 替代 OpenAPI、Avro、Protobuf 等领域 schema；引用这些规范并补充其周边知识。
- 不要求特定云、模型、agent framework、搜索引擎或可视化器。
- 不因消费者不认识某个 `type` 或扩展字段而删除信息或判定 bundle 无效。
