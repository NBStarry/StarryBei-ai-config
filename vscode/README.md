# VS Code 配置

本目录保存可公开、可跨机器复用的 VS Code 用户设置片段。

## Codex 终端 Tab 标题

将 `settings.json` 中的设置合并到当前 VS Code 用户设置，不要覆盖已有文件：

- macOS：`~/Library/Application Support/Code/User/settings.json`
- Windows：`%APPDATA%\Code\User\settings.json`
- Linux：`~/.config/Code/User/settings.json`

该设置让 VS Code 使用终端进程发送的 OSC 标题序列。配合
`codex/config.toml.example` 中的：

```toml
[tui]
terminal_title = ["activity", "thread-title"]
```

重启 Codex 后，终端 Tab 在空闲时显示会话名，运行时显示类似
`⠋ session-name` 的活动状态。会话名通常在第一轮处理后生成。

`${sequence}` 也会显示普通 shell 自己发送的标题。oh-my-zsh 默认标题包含用户名、
主机名和完整路径，可能过长；本机使用的“仅显示当前目录名”规则由
[`hzb-terminal-config/zsh/.zshrc`](https://github.com/NBStarry/hzb-terminal-config/blob/main/zsh/.zshrc)
统一管理，避免在 AI 工具配置仓库中重复维护 shell 逻辑。
