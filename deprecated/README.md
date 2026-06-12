# Deprecated / 废案

已废弃的方案。保留代码供参考，不再维护。

## QQ 双向通信方案（`qq/`）

**废弃原因：** 腾讯风控频繁检测机器人账号并强制下线，依赖非官方的 LLOneBot 插件（NTQQ 插件），无法保证稳定性。曾迁移到 Telegram，后者现也已弃用。

### 废弃文件

| 文件 | 原路径 | 说明 |
|------|--------|------|
| `qq/notify-qq.sh` | `scripts/notify-qq.sh` | QQ 出站通知脚本（通过 LLOneBot HTTP API） |
| `qq/qq-bridge.sh` | `scripts/qq-bridge.sh` | QQ 入站桥接守护进程（通过 LLOneBot WebSocket） |
| `qq/notification-qq.json` | `hooks/notification.json` | QQ 通知 hook 配置模板 |
| `qq/settings-qq.json` | `configs/settings.json` | QQ 版全局设置（含 hook 配置） |

## Telegram 双向通信方案

**废弃原因：** 仓库改造为多工具配置库时，不再需要远程手机通知/桥接功能。相关脚本（`notify-telegram.sh`、`telegram-bridge.sh`、`notification.telegram.json`、`telegram.conf.example`）已在 commit `085144c` 从主线移除，如需可从该提交的父提交 `085144c^` 恢复。

## sync-configs.sh

**废弃原因：** 旧的「复制 + 双向同步 + 脱敏」机制已被 `install.sh` 的 symlink 模式取代。保留此脚本仅供参考其脱敏正则逻辑。

### 相关提交历史

| Commit | 日期 | 说明 |
|--------|------|------|
| `aedcfff` | 2026-02-06 | feat: QQ 消息通知 (notify-qq.sh) |
| `6beec01` | 2026-02-06 | feat: QQ 消息桥接 (qq-bridge.sh) |
| `4c8ce1d` | 2026-02-09 | feat: 迁移到 Telegram（QQ 方案被替代） |
| `085144c` | 2026-04-12 | chore: 移除全部 Telegram 内容 |
