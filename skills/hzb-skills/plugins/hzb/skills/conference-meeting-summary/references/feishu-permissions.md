# jushen-team app scope 状态（截至 2026-05-18 验证）

## 已开通

| Scope | 用途 | 怎么用到 |
|---|---|---|
| `docs:document:create` | 创建 docx 文档 | `docs +create` |
| `docs:document:write_only` | 写文档内容 | `docs +update --command append/str_replace/...` |
| `docs:document:readonly` | 读文档内容 | `docs +fetch` |
| `docs:document.media:upload` | 上传图片/文件并插入到文档 | `docs +media-insert` |
| `docs:permission.member:create` | 给指定用户添加文档协作者权限 | `drive permission.members create` |
| `space:document:delete` | 删除文档（清理写错的版本） | `drive +delete --type docx` |

## 已知不可用 / 需要时再申请

| Scope | 何时需要 |
|---|---|
| `drive:drive.metadata:readonly`（bot） | 用 bot 列云空间文件夹时 |
| `space:document:move` | 移动文档到指定文件夹 |
| `wiki:*` | 把文档挂到知识库节点 |

## 怎么申请新 scope

Console URL 格式（替换 `<scope>` 为冒号转 `%3A`）：
```
https://open.feishu.cn/page/scope-apply?clientID=cli_aa8b1d3b35fb1cd8&scopes=<scope-url-encoded>
```

多个 scope 用 `%20` 拼接（空格 url-encoded）。

如果 lark-cli 报 `App scope not enabled: required scope X [99991672]`，error 里会带 `console_url`，直接点开就能申请。审批通过后立刻生效，无需重启。

## 用户访问授权（4Paradigm tenant）

已缓存（示例占位，实际值请用 lark-cli 查询自己的身份）:
- open_id（personal app `<APP_ID>` 视角）: `ou_<YOUR_OPEN_ID>`
- union_id（跨 app 稳定）: `on_<YOUR_UNION_ID>`
- tenant_key: `<YOUR_TENANT_KEY>`
- 中文名: `<YOUR_NAME>` / localized_name: `<YOUR_LOCALIZED_NAME>`

授权命令模板：
```bash
lark-cli drive permission.members create \
  --profile jushen-team --as bot \
  --params '{"token":"<docx_token>","type":"docx","need_notification":"false"}' \
  --data '{"member_id":"<YOUR_UNION_ID>","member_type":"unionid","perm":"full_access","perm_type":"container","type":"user"}' \
  --yes
```

**永远走 union_id 不走 open_id**：union_id 跨 app 稳定，open_id 是 app-scoped 的。

## 两个 Feishu tenant 注意事项

<YOUR_NAME>的工作目录涉及两套 Feishu 身份：

| Profile | App ID | tenant 域名 | 默认登录态 |
|---|---|---|---|
| `<YOUR_APP_ID>` | 个人 / 4Paradigm | <YOUR_TENANT>.feishu.cn | user logged-in |
| `jushen-team` | 具身智能团队 | <JUSHEN_TENANT>.feishu.cn | bot only（无 user） |

**本目录所有 lark-cli 操作默认 --profile jushen-team**（CLAUDE.md 项目规则）。

bot 创建的 doc 默认只有 bot 可见，必须显式调用 `permission.members create` 把用户加进去。否则用户打开 URL 是 404 或权限不足。
