# Skills

本仓库不再保存第三方 skill 快照。Skill 源码由各自的外部 marketplace 维护，本仓库只记录安装与 Dashboard 聚合所需的声明。

- `config/skill-plugins.json`：新机器需要注册和安装的 Claude/Codex plugins。
- `config/external-skill-sources.json`：GitHub Pages Dashboard 读取的公开 skill 源。
- `claude/configs/recommended-skills.json`：通过 `npx skills` 安装的独立 skill 清单。
- `claude/configs/recommended-plugins.json`：更广泛的可选插件盘点，不等同于默认安装集合。

运行仓库安装器会安装 `config/skill-plugins.json` 中声明的插件：

```powershell
pwsh -File .\install.ps1
```

只更新配置、不访问 marketplace：

```powershell
pwsh -File .\install.ps1 -SkipSkillPlugins
```

Linux/macOS 对应使用 `bash install.sh` 或 `bash install.sh --skip-skill-plugins`。
