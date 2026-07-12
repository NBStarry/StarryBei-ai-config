# Scripts

Claude Code 自定义脚本。

## 统一配置管理

`config.ps1` 读取 `config/manifest.json`，在 Windows PowerShell 中提供可审查、可回滚的配置迁移闭环：

```powershell
pwsh -File .\scripts\config.ps1 doctor
pwsh -File .\scripts\config.ps1 plan
pwsh -File .\scripts\config.ps1 apply
pwsh -File .\scripts\config.ps1 verify
pwsh -File .\scripts\config.ps1 rollback
```

`plan` 不写文件；`apply` 只处理 `missing` / `drifted` 资源并写事务日志；`seed` 目标一旦存在就不覆盖。自动化场景可加 `-Json`，测试或迁移其他 Home 可加 `-HomePath <path>`。

## 外部 Skill Plugins

`install-skill-plugins.ps1` / `install-skill-plugins.sh` 读取 `config/skill-plugins.json`，用 Claude Code 和 Codex 的原生 marketplace/plugin 命令补齐外部 skills。它们会跳过已存在的 marketplace 和已安装 plugin，不改变现有启用状态。

只查看计划、不访问网络或修改工具状态：

```powershell
pwsh -File .\scripts\install-skill-plugins.ps1 -Plan
```

```bash
bash scripts/install-skill-plugins.sh --plan
```

## 本地完整 Dashboard

从仓库根目录执行：

```powershell
pwsh -File .\scripts\start-local-dashboard.ps1
```

本地版复用 `site/` 前端，但由 `local-dashboard-server.mjs` 在启动时扫描当前机器：

- Claude 已安装插件及其 skills
- `~/.claude/skills`、`~/.codex/skills`、`~/.agents/skills`
- Claude/Codex 的本地 settings、全局指令、插件安装清单
- `config/manifest.json` 与本机目标的逐项状态（installed / missing / drifted）

服务只监听 `127.0.0.1:4173`，数据仅保存在进程内存。`.credentials.json`、`auth.json` 等认证文件不会读取，敏感配置字段会显示为 `[REDACTED]`。按 Ctrl+C 停止；可用 `-Port 4180` 更换端口，或用 `-NoBrowser` 禁止自动打开浏览器。

在线 GitHub Pages 使用登记的公开外部来源生成 `site/data.json`，不会包含上述本机数据。

## statusline.sh

自定义状态栏脚本，在 Claude Code 终端底部显示丰富的上下文信息。

### Features / 功能

- 显示 `用户名@主机名:当前目录`（绿色/蓝色）
- 显示当前使用的模型名称（青色）
- 显示 Git 当前分支（黄色）
- 显示上下文窗口使用率，带颜色编码：
  - 绿色：< 50%（充裕）
  - 黄色：50%-80%（注意）
  - 红色：>= 80%（紧张）

### Preview / 效果预览

```
user@mac:~/projects/myapp Claude Opus 4.6 (main) [ctx:34%]
```

### Dependencies / 依赖

- `jq` - JSON 解析工具
- `git` - 用于获取分支信息

```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq
```

### Installation / 安装

```bash
cp statusline.sh ~/.claude/statusline.sh
chmod +x ~/.claude/statusline.sh
```

确保 `~/.claude/settings.json` 中包含：

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash ~/.claude/statusline.sh"
  }
}
```

### How It Works / 工作原理

Claude Code 通过 stdin 向状态栏脚本传入 JSON 数据，包含模型信息和上下文窗口用量等。脚本读取这些数据，结合本地环境信息（用户名、主机名、目录、Git 分支），组合输出带 ANSI 颜色编码的状态栏字符串。

---

## sync-configs.sh

双向同步 `~/.claude/` 本地配置与仓库 `configs/` 目录。配合 GitHub Pages Dashboard 实现远程配置管理。

### Features / 功能

- **push**：本地 → 仓库，覆盖 `configs/` 下的对应文件
- **pull**：仓库 → 本地，自动备份原文件到 `~/.claude/backups/`
- **status**：彩色显示同步状态（IN SYNC / OUT OF SYNC / MISSING）
- **diff**：显示完整 unified diff（本地 vs 仓库）

### Synced Files / 同步文件

| 本地路径 | 仓库路径 | 说明 |
|----------|----------|------|
| `~/.claude/CLAUDE.md` | `configs/CLAUDE.md` | 全局指令 |
| `~/.claude/settings.json` | `configs/settings.json` | 全局设置（hooks、plugins、model） |
| `~/.claude/settings.local.json` | `configs/settings.local.json` | 本地权限覆盖 |

### Usage / 使用方式

```bash
# 查看同步状态
bash scripts/sync-configs.sh status

# 推送本地配置到仓库
bash scripts/sync-configs.sh push

# 从仓库拉取配置到本地
bash scripts/sync-configs.sh pull

# 查看完整差异
bash scripts/sync-configs.sh diff
```

### Workflow / 工作流

```
本地修改配置 → sync-configs.sh push → git commit + push → GitHub Actions 部署 → Dashboard 可见
Dashboard 编辑 → GitHub 原生编辑页提交 → git pull → sync-configs.sh pull → 本地生效
```

### Dependencies / 依赖

- `diff` — 文件比较（macOS/Linux 自带）
