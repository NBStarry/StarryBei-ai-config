# VALSE 2026 · A2 Workshop — VLA 具身智能强化学习系统演进

> **讲者**：于超（清华大学深圳国际研究生院助理教授）
> **时间**：2026-05-09 09:03 · 武汉 · VALSE 2026 Workshop VLA Session
> **时长**：31:07 · 126 段 · 26 张现场 slide
> **钉钉闪记原文**：https://shanji.dingtalk.com/app/transcribes/76327569643238353231393130395f363538343634363534325f32

---

## 一句话总览

围绕"具身智能 = 强化学习 + 真实世界交互"这一假设，于超团队用一年时间完成从 **机理验证 → 仿真系统 RLinf → 算法层 π_RL → 真机端云系统 RLinf-USER → 世界模型训练 WoVR** 的五段式演进，目标是把具身智能基础设施做成"像使用 GPU 一样使用机器人"。

---

## 演进时间线

| 阶段 | 时间 | 名字 | 核心问题 | 关键产物 |
|---|---|---|---|---|
| Step 1 | 25.2–25.5 | 机理验证 | RL 相比 SFT 在 VLA 上有没有优势？ | NeurIPS 25 论文，确认语义/执行泛化 RL 优于 SFT |
| Step 1.5 | 25.5–25.6 | 系统拉胯 | 现有 RL 框架（VeRL/Slime/ROLL/AReaL/AsyncFlow）为何不适配具身？ | 流程异构 + 仿训推一体 + 端云协同三大瓶颈 |
| Step 2 | 25.6–25.9 | RLinf v0.1 | 算法驱动的系统设计 | Macro-to-Micro Flow（M2Flow）编程范式，OSDI 26 |
| Step 2.5 | 25.6–25.10 | π_RL 算法 | 流式 VLA（π 系列）的 likelihood 无法直接算，如何 RL 微调？ | Flow-Noise / Flow-SDE 两种范式，4 数据集 30–50% 提升（arXiv 2510.25889） |
| Step 3 | 25.11–26.2 | RLinf-USER | 仿真→真实的虚实差距 | 端云系统 USER（Unified and Extensible System for Real-world Online Policy Learning in Embodied AI） |
| Step 3.5 | 25.11–26.2 | WoVR | 真机代价太高，能否在世界模型里训练？ | 三层约束（仿真层/交互层/对齐层），世界模型性能超越 Cosmos-Predict2、OpenSora |

---

## 1. 为什么做具身智能 + 强化学习

**核心命题**：不是"重新发明机器人"，而是**重新思考智能在物理世界如何存在**——把智能边界从数字空间扩展到物理空间。

**学习范式选择**：

- **离线（SFT）**："纸上得来终觉浅"——离线数据与真机部署存在分布偏差，灵巧性、泛化性差强人意
- **在线（RL）**："绝知此事要躬行"——从真实交互中学习，类比婴儿学叠积木：父母示范 + 自己试错 → 真正习得

**因此 RL 是具身智能的关键路径**（前提是基础设施跟得上）。

---

## 2. Step 1 机理验证：RL vs SFT in VLA

> 25.2 DeepSeek-R1 验证 RL 对语言模型有显著智能提升。问题：RL 对具身大模型（VLA）有没有同样的效果？

**实验设计**：用 PPO 微调 OpenVLA，对照监督微调（SFT）模型，从三个维度做 OOD 测试：

| 泛化维度 | 测试设置 | RL 相对 SFT 的 OOD 性能下降幅度 |
|---|---|---|
| 视觉泛化 | 不同材质、不同背景 | 与 SFT 相近（≈40% 下降）→ **视觉泛化能力主要由 SFT 决定** |
| 语义泛化 | 不同物品、不同指令 | RL 明显占优 |
| 执行泛化 | 不同位置、不同操作 | RL 仅下降 16%，SFT 下降 40%+ → **执行层面提升 >30%** |

**结论**：RL 不能替代 SFT 做视觉理解，但**在语义和执行的泛化上是 SFT 不可替代的**。论文进入 NeurIPS 25：*"What Can RL Bring to VLA Generalization? An Empirical Study"*（Jijia Liu, Feng Gao, Bingwen Wei, Xinlei Chen, Qingnan Liao, Yi Wu, Chao Yu, Yu Wang）。

---

## 3. Step 1.5 系统拉胯：现有 RL 框架为什么不能用

机理可行，但训一个模型要一周——"系统大哥上加个速"做了一周发现这是**全新领域**。**三大瓶颈**：

**① 算法流程异构**：
- 语言/数字空间 RL 几乎都是 on-policy（PPO/GRPO 变种）+ 高度一致的训练流程
- 具身领域 on-policy 样本效率不够，业界（如 Physical Intelligence）转向 off-policy；流派未收敛
- 现有 RL 框架（VeRL、Slime、ROLL 等）的 Collected mode、AReaL/AsyncFlow 的 Disaggregated mode 都满足不了

**② 仿训推一体化**：
- 具身 RL 同时需要仿真器（GPU 渲染 + 物理碰撞计算）、训练、推理三个模块
- 仿真器抢占 GPU，资源调度复杂

**③ 端云协同**：
- 推理：3–4B 模型一张 4090 即可
- 训练：必须 A100/A800 八卡 → 机房集群，机器人在现场 → 端云通信、数据效率、人在环路全部都是系统问题

---

## 4. Step 2 RLinf 系统（v0.1, 25.6–25.9）

**定位**：首个面向具身智能的高灵活大规模 RL 框架，**算法驱动的系统设计**。

### 4.1 六层架构

```
用户层 → 任务层 → 执行层 → 调度层 → 通信层 → 硬件层
（用户只关心前两层，剩余由系统自动映射）
```

### 4.2 核心创新：M2Flow（Macro-to-Micro Flow Transformation）

新型 RL 编程范式，**解耦上层算法逻辑与底层系统优化**：
- 用户像写 PyTorch（所见即所得）一样写算法
- 系统层自动转换为 TensorFlow 风格的全图优化执行

成果发表于 **USENIX OSDI 26**（"RLinf: Flexible and Efficient Large-scale Reinforcement Learning via Macro-to-Micro Flow Transformation"）。

### 4.3 三种内置调度模式

| 模式 | 资源分配 | 适用场景 | 痛点 |
|---|---|---|---|
| **共享式（Shared）** | 同一时刻一个组件占满 GPU | 串行任务 | 具身需要 actor↔env 持续交互，效率低 |
| **分离式（Disaggregated）** | 提前固定卡分配（如 2 卡 A、2 卡 B） | 简单算法 | 利用率低 |
| **混合式（Hybrid）** ⭐ | actor & env 分离 + 数据队列 + 训练共享；做流水线切分 | 具身 RL | 保持 on-policy 形式同时压榨显卡利用率 |

### 4.4 算法层补丁：π_RL（Step 2.5）

RLinf v0.1 主要面向 OpenVLA 等自回归 VLA。但业界主流已转向 **流式 VLA（π_0、π_0.5、GR00T）**——这类模型在 VLM 后挂一个 Action Expert（flow-based / production-style）。**问题**：flow-based 模型的 likelihood 难以闭式计算，无法直接套 on-policy RL。

**解法**：提出两种范式（论文 *"π_RL: Online RL Fine-tuning for Flow-based VLA Models"*，arXiv:2510.25889）：

| 方法 | 思路 |
|---|---|
| **Flow-Noise** | 向网络注入噪声让分布具备随机性 → 可用 on-policy 算法微调 |
| **Flow-SDE** | 把 flow 转换为 SDE 表达 → 在数学上等价，可用 off-policy 算法 |

**效果**：训三个模型（π_0 / π_0.5 / GR00T）× 四个测试集（**LIBERO / ManiSkill / MetaWorld / Calvin**），30%–50% 性能提升；**R2S2R**（Real-to-Sim-to-Real）实现真机部署测试。

### 4.5 RLinf 支持矩阵（截至发布时）

| Simulators | Models | Algorithms | Real-world Robotics | Data Collection |
|---|---|---|---|---|
| ManiSkill, LIBERO, LIBERO-Pro & Plus, RoboTwin, RoboVerse, BEHAVIOR, MetaWorld, IsaacLab, CALVIN, RoboCasa, Franka-Sim, EmbodiedChain | π_0 / π_0.5 / OpenVLA / LingBot-VLA / OpenVLA-OFT / GR00T / Dexbotic / StarVLA / Qwen2.5-VL / Qwen3-VL / OpenSora / Wan / MLP-Policy / CNN-Policy / ResNet | IQL / GRPO / PPO / DAPO / Reinforce++ / SAC / CrossQ / RLPD / SAC-Flow / DSRL / RECAP[CFG] / Full-param SFT / LoRA SFT / VLM SFT / DAgger / HG-DAgger | Franka Arm + Intel RealSense + Stereolabs ZED + Franka Hand + Robotiq 2F-85/2F-140; XSquare Turtle2; Dual-Franka | GELLO, SpaceMouse |

---

## 5. Step 3 RLinf-USER：真实世界在线策略学习（25.11–26.2）

**触发点**：25.10 发现仿真世界与真实世界存在**不可弥合的虚实差距**——仿真假设（可复制 / 可加速 / 交互成本低 / 物理约束弱）在真机上全部反过来。

**核心命题**：规模化、真实世界、可扩展的在线策略学习 = **系统与算法深度耦合**的复杂问题。在 RLinf 之上做增量升级 → **RLinf-USER**（Unified and Extensible System for Real-World Online Policy Learning in Embodied AI）。

### 5.1 系统层 · 设计 1：统一硬件抽象层

- 把机器人硬件与计算硬件放到同一层级管理
- 原话："**像使用 GPU 一样使用机器人**"——单机/多机即插即用，分布式数据通道（Distributed Data Channel）+ 硬件注册发现 + 云边隧道（Cloud-Edge Tunneling Network）
- 实验：4 台不同结构机器人（Franka × 方柱 × 软体）同时跨域训练，习得模型天然具备跨本体控制能力

### 5.2 系统层 · 设计 2：自适应通信平面

- 具身大模型端云协同训练 → 跨域互通困难、集中式通信开销大
- 设计：集中式 + 分布式两种 Master-Rollout-Robot 拓扑可切换；网络隧穿 + 分布式数据通道
- 实验：**北京-深圳千里端云协同训练**，跨域单 episode 生成时间从 70 秒降到 20 秒（**3 倍提速**）；同城对比 17 秒 vs 20 秒，几乎抹平跨域开销

### 5.3 算法层 · 设计 3：全异步训练架构

- 真实世界训练数据效率是第一瓶颈
- 解耦 数据生成 / 传输 / 训练 / 权重同步
- 同步 vs 异步对比：训练吞吐提升 **5.7×**（Sync Pipeline → Async Pipeline）

### 5.4 算法层 · 设计 4：持久化缓存感知缓冲区

- 长周期在线训练数据量持续增长，**纯内存放不下、纯磁盘高频采样跟不上**
- 设计：内存 + 磁盘协同持久化 + 动态索引 + 异步存取，TB 级数据近零等待访问
- 实验：断点续训后**蓝/绿曲线与未中断完美贴合**（No forgetting），多任务持续学习不退化

### 5.5 USER 真机效果（Pick-and-Place / Table Clean-up）

| 任务 | Online Training 前 | Online Training 后 |
|---|---|---|
| Pick-and-Place（RLPD + HG-DAgger，π_0 backbone） | 39/60 | **58/60** |
| Table Clean-up（HG-DAgger，π_0 backbone） | 9/20 | **16/20** |

---

## 6. Step 3.5 WoVR：在世界模型里训练（真机代价的破局思路）

**核心思路**：真机训练贵 → 把真实世界变成**世界模型** → 在世界模型里做闭环策略训练 → 迁回真机。

**三层约束**（解决自回归世界模型闭环时的"幻觉"）：

| 层级 | 设计 |
|---|---|
| 仿真层 | Stabilized Action-Conditioned World Model — 让世界模型稳定可控（Controllable Simulator） |
| 交互层 | Hallucination-Aware Policy Optimization in Imagination — 引入关键帧初始化技术，避免仅靠初始帧"想象" |
| 对齐层 | Policy-Aligned Co-Evolution — 策略与模拟器共同进化 |

**实验**（基于 Franka Emika Panda & AgileX Piper 真机）：
- 世界模型性能（FID / LPIPS / FVD 等）超越 Cosmos-Predict2、OpenSora
- 仿真环境下，基于 WoVR 后训练的策略显著优于 OpenVLA-OFT / GRPO online / WMPO
- 真机：仅引入少量轨迹，无需在线交互，仅在世界模型中训练即可实现策略性能提升

---

## 7. 生态、合作与"为什么这件事重要"

**开源数据（公开半年）**：GitHub `RLinf/RLinf` 仓库 **3.3k+ stars / 420+ forks**，全开源；ReadTheDocs 提供 Quickstart、Tutorials、Example Gallery、Blog、APIs、FAQs。

**产业合作伙伴**：
- 算法/模型：英伟达（NVIDIA）、华为、DEXMAL、AgileX、引望、摩尔线程、Robbyant、地瓜机器人、Giga AI、AMD、X Square Robot、DexForce、PsiBot
- 典型用户场景：
  - **NVIDIA × RLinf**：完成微创手术器械组装任务（GR00T + online RL post-training，登上央视）
  - **极佳科技**：在 RLinf 上开 π_step-NFT
  - **地瓜机器人**：模型部署平台支持 RLinf 框架
  - **原力灵机**：Dexbotic 模型后训练使用 RLinf

**愿景**：打造**下一代具身智能训练基础设施**，几乎以公益方式向研究界与产业界开放。

---

## 8. 与钉钉闪记 AI Summary 的差异（查漏补缺）

闪记自动生成的 AI Summary 在结构上覆盖了主线，但**命名实体识别错误较多**（语音转写问题）。下表列出主要纠错与补充：

| AI Summary 写法 | 实际正确名称 | 纠错来源 |
|---|---|---|
| "儿童"系统 / "儿童规则" | **RLinf** / **RLinf-USER** | slide 8375、8383（RL 被识别成"儿童"） |
| "看尔苗" | **π_RL** | slide 8377 标题 |
| Blue Noise / Blue11 | **Flow-Noise / Flow-SDE** | slide 8377 |
| M6 / Word / Topic 四数据集 | **LIBERO / ManiSkill / MetaWorld / Calvin** | slide 8377 |
| production xaster | **Action Expert** | slide 8376（Action Expert: Fast, Interact with Physical World） |
| v2a / VRA / vra 模型 | **VLA**（Vision-Language-Action） | 上下文 |
| VL / Space Mobile | **VeRL / Slime / ROLL**（Collected mode）+ **AReaL / AsyncFlow**（Disaggregated mode） | slide 8373 |
| 3 星具身智能项目 / 400+ fork | **3.3k+ stars / 420+ forks** | slide 8393 |
| 医疗器械组装 | **微创手术器械组装** | slide 8394 NVIDIA 用户场景 |
| 微量 / AMB | **NVIDIA / AMD** | slide 8394 合作伙伴矩阵 |
| OSDI 顶会 | **OSDI 26**（USENIX）+ 论文 *"RLinf: Flexible and Efficient Large-scale RL via Macro-to-Micro Flow Transformation"* | slide 8375 |
| Luo 编程范式 | **M2Flow（Macro-to-Micro Flow Transformation）** | slide 8375 |
| （未提）π_RL 论文 | **arXiv:2510.25889**（*π_RL: Online RL Fine-tuning for Flow-based VLA Models*） | slide 8377 |
| （未提）NeurIPS 25 RL vs SFT 论文 | *"What Can RL Bring to VLA Generalization? An Empirical Study"*（Jijia Liu 等） | slide 8371 |
| （未提）USER 全称 | **Unified and Extensible System for Real-World Online Policy Learning in Embodied AI** | slide 8385 RLinf-USER 系统层设计 1 |
| （未提）WoVR | **WoVR**：Step 3.5 真机代价破局——在世界模型里训练；三层约束设计 | slide 8391、8392 |
| （未提）R2S2R | **R2S2R**（Real-to-Sim-to-Real）实现真机部署测试 | slide 8377 |
| GitHub 链接 | **https://github.com/RLinf/RLinf** ; ReadTheDocs `https://rlinf.readthedocs.io/en/latest` | slide 8393 |

**结构层面补充**：闪记 AI Summary 缺失了 **WoVR（Step 3.5）整个章节**、**USER 真机数据表（Pick-and-Place / Table Clean-up）**、**RLinf 支持矩阵的具体清单**、**π_RL 的论文/方法细节**。本文档基于 transcript + 26 张现场 slide 已补齐。

---

## 9. 个人 take-aways（4Paradigm 视角）

- **算法驱动的系统设计**这一定位值得借鉴——具身领域 RL 流派未收敛、不能用语言模型框架直接搬，必须算法+系统协同
- **混合式调度** + **全异步训练**是真机 RL 框架的两个关键支柱
- **"像使用 GPU 一样使用机器人"** 是基础设施层的明确口号，对应到我们做 G1 应该思考：何时把机器人也抽象成可池化的计算资源
- **WoVR 思路**对真机训练贵的痛点是一种破局思路，可作为我们世界模型方向的对标参考
- **R2S2R**（Real-to-Sim-to-Real）+ **π_RL 在 flow-based VLA 上的 RL 微调能力**是值得继续跟进的开源工程
