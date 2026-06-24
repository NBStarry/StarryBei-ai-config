---
domain: cloud.phanthy.com
aliases: [PhanRouter, phanthy, 具身智能团队网关]
updated: 2026-06-22
---
## 平台特征
- PhanRouter 是基于 **New-API**(one-api 系)的 LLM 网关控制台,页脚"设计与开发由 New API"。
- 控制台路径:`https://cloud.phanthy.com/phanrouter/console`,登录态走浏览器 cookie。
- API 基址:`https://cloud.phanthy.com/phanrouter/api`(注意带 `/phanrouter` 前缀,根路径 `/api/...` 是 404)。
- 管理接口鉴权:cookie 会话 **或** 访问令牌,且**必须**额外带 `New-Api-User: <userId>` 头,否则报"未提供 New-Api-User"。

## 有效模式(已验证 2026-06-22)
- 当前用户 id 在 `localStorage.user` JSON 里(本账号 id=73)。
- `GET /api/user/self` (带 New-Api-User) → `data.quota` 当前余额、`data.used_quota` 历史消耗、`data.request_count`。金额 = quota / `quota_per_unit`(localStorage 里=500000,即 ÷500000 得 USD)。
- `GET /api/user/token` (带 New-Api-User) → 生成/重置**系统访问令牌**(管理 API 用),返回 `data` 为令牌串。⚠ 会使旧的访问令牌失效;与「令牌管理」里的 `sk-` 中转令牌互相独立。
- 独立程序鉴权:`Authorization: Bearer <访问令牌>` + `New-Api-User: <id>`,curl 无 cookie 实测可取 /api/user/self。
- `GET /api/pricing` → **公开,无需鉴权**。返回 `data`(模型列表,含 `model_name`/`vendor_id`/`model_ratio`/`enable_groups`)、`vendors`(id→name 厂商映射)、`group_ratio`、`usable_group`。

## 已知陷阱
- `sk-` 开头是 **中转令牌**(/v1 relay 用),调管理 API 报"access token 无效"。管理 API 要的是系统访问令牌(非 sk- 前缀)。
- pricing 里很多模型 `vendor_id` 缺失,且模型名是 PhanRouter 改名版:前缀 `PR-A`=Anthropic、`PR-O`=OpenAI、`PR-G`/`PR-Ge`=Google、`PR-X`=xAI、`PR-V`=视频生成(按版本号可反推,如 PR-O-5=GPT-5、PR-A-Ultra-4.8=Claude Opus 4.8)。按来源分类需结合 vendor_id 映射 + 名称前缀推断。
