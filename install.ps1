# Windows installer for StarryBei-ai-config (PowerShell port of install.sh).
#
# Links repo files into %USERPROFILE%\.claude and %USERPROFILE%\.codex.
#   - Files   -> symbolic links (New-Item SymbolicLink). Needs Windows
#               Developer Mode ON, or an elevated (Run as administrator) shell.
#   - Folders -> directory junctions (New-Item Junction). No privilege needed,
#               works across volumes (repo on A:, home on C:).
# Existing targets are backed up first. Sensitive files are SEEDED from .example
# templates (never overwritten if a real file already exists).
#
# Usage:  powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1

$ErrorActionPreference = 'Stop'

$Repo       = $PSScriptRoot
$ClaudeHome = Join-Path $env:USERPROFILE '.claude'
$CodexHome  = Join-Path $env:USERPROFILE '.codex'
$Stamp      = Get-Date -Format 'yyyyMMdd-HHmmss'
$BackupDir  = Join-Path $env:USERPROFILE ".ai-config-backup-$Stamp"
$SymlinkFailed = $false

# Probe symlink capability ONCE up front. If we can't create symlinks (no
# Developer Mode and not elevated), we must NOT back up/destroy existing files.
# Use `mklink` (cmd builtin): unlike Windows PowerShell 5.1's
# `New-Item -ItemType SymbolicLink`, it honors Developer Mode and creates
# symlinks WITHOUT elevation (passes the unprivileged-create flag).
function New-FileSymlink([string]$link, [string]$target) {
  cmd /c "mklink `"$link`" `"$target`"" > $null 2>&1
  return (Test-Path -LiteralPath $link)
}
function Test-SymlinkCapability {
  $probe  = Join-Path $env:TEMP ("symprobe-" + [System.IO.Path]::GetRandomFileName())
  $target = Join-Path $env:TEMP ("symtgt-"  + [System.IO.Path]::GetRandomFileName())
  Set-Content -LiteralPath $target -Value 'x' -Encoding ascii
  try {
    $ok = New-FileSymlink $probe $target
    if ($ok) { Remove-Item -LiteralPath $probe -Force }
    return $ok
  } finally {
    Remove-Item -LiteralPath $target -Force -ErrorAction SilentlyContinue
  }
}
$CanSymlink = Test-SymlinkCapability

function Backup-IfExists([string]$dest) {
  if (Test-Path -LiteralPath $dest) {
    if (-not (Test-Path -LiteralPath $BackupDir)) { New-Item -ItemType Directory -Path $BackupDir | Out-Null }
    Move-Item -LiteralPath $dest -Destination $BackupDir -Force
    Write-Host "backed up $dest -> $BackupDir\"
  }
}

# Link a single FILE via symbolic link (repo owns the canonical copy).
# If symlinks are unavailable, leave any existing file untouched (don't destroy
# a working config) and flag that Developer Mode is needed.
function Link-File([string]$src, [string]$dest) {
  if (-not (Test-Path -LiteralPath $src)) { Write-Host "SKIP (missing source): $src"; return }
  if (-not $CanSymlink) {
    $script:SymlinkFailed = $true
    Write-Host "SKIP     symlink $dest (needs Developer Mode or admin; left as-is)" -ForegroundColor Yellow
    return
  }
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
  Backup-IfExists $dest
  if (New-FileSymlink $dest $src) {
    Write-Host "linked   $dest -> $src"
  } else {
    $script:SymlinkFailed = $true
    Write-Host "FAILED   symlink $dest" -ForegroundColor Yellow
  }
}

# Link a DIRECTORY via junction (no privilege needed, cross-volume OK).
function Link-Dir([string]$src, [string]$dest) {
  if (-not (Test-Path -LiteralPath $src)) { Write-Host "SKIP (missing source): $src"; return }
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
  Backup-IfExists $dest
  New-Item -ItemType Junction -Path $dest -Target $src | Out-Null
  Write-Host "junction $dest -> $src"
}

# Create real from example ONLY if real doesn't exist (never overwrites).
function Seed-File([string]$example, [string]$real) {
  if (-not (Test-Path -LiteralPath $example)) { Write-Host "SKIP (missing template): $example"; return }
  if (Test-Path -LiteralPath $real) { Write-Host "kept     $real (already exists, not overwritten)"; return }
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $real) | Out-Null
  Copy-Item -LiteralPath $example -Destination $real
  Write-Host "seeded   $real <- $example   (FILL IN real values)"
}

Write-Host "Installing AI coding tool configs from $Repo"
Write-Host ""

# -- Claude Code: files (symlinks) ------------------------------------------
# Windows uses settings.windows.json (PowerShell statusline + proxy in env)
# instead of the macOS settings.json (bash/jq statusline).
Link-File (Join-Path $Repo 'claude\configs\settings.windows.json') (Join-Path $ClaudeHome 'settings.json')
Link-File (Join-Path $Repo 'claude\configs\CLAUDE.md')             (Join-Path $ClaudeHome 'CLAUDE.md')
Link-File (Join-Path $Repo 'claude\scripts\statusline.ps1')        (Join-Path $ClaudeHome 'statusline.ps1')

# -- Claude Code: hzb-skills marketplace (directory junction) ----------------
Link-Dir (Join-Path $Repo 'skills\hzb-skills') (Join-Path $ClaudeHome 'hzb-skills')

# -- Seed sensitive real files from sanitized templates ----------------------
$Hzb = Join-Path $Repo 'skills\hzb-skills\plugins\hzb'
Seed-File (Join-Path $Hzb 'commands\connect-internal.md.example')        (Join-Path $Hzb 'commands\connect-internal.md')
Seed-File (Join-Path $Hzb 'commands\connect-internal-backup.md.example') (Join-Path $Hzb 'commands\connect-internal-backup.md')

# -- Register hzb marketplace (idempotent best-effort) -----------------------
$claudeCli = Get-Command claude -ErrorAction SilentlyContinue
if ($claudeCli) {
  try {
    & claude plugin marketplace add (Join-Path $ClaudeHome 'hzb-skills') 2>&1 | Out-Null
    Write-Host "registered hzb-skills marketplace"
  } catch {
    Write-Host "NOTE: run once to register hzb: claude plugin marketplace add `"$ClaudeHome\hzb-skills`""
  }
} else {
  Write-Host "NOTE: 'claude' not on PATH. Register hzb later with:"
  Write-Host "      claude plugin marketplace add `"$ClaudeHome\hzb-skills`""
}

Write-Host ""
Write-Host "NOTE: GLM backend config is not seeded (API key not in repo)."
Write-Host "      To use it:  Copy-Item '$Repo\claude\configs\settings.glm.json.example' '$ClaudeHome\settings.glm.json'"
Write-Host "      then fill in ANTHROPIC_AUTH_TOKEN."

# -- Codex CLI: shared skills (directory junctions) --------------------------
foreach ($s in 'codex-review','conference-meeting-summary','web-access','save-memory-before-compact') {
  $sdir = Join-Path $Hzb "skills\$s"
  if (Test-Path -LiteralPath $sdir) {
    Link-Dir $sdir (Join-Path $CodexHome "skills\$s")
  }
}

Write-Host ""
if (-not (Test-Path -LiteralPath (Join-Path $CodexHome 'config.toml'))) {
  Write-Host "NOTE: no ~\.codex\config.toml found."
  Write-Host "      Copy-Item '$Repo\codex\config.toml.example' '$CodexHome\config.toml'   # then set trusted project paths"
}

# -- done --------------------------------------------------------------------
Write-Host ""
Write-Host "Done."
if (Test-Path -LiteralPath $BackupDir) { Write-Host "Backup of replaced files: $BackupDir" }
if ($SymlinkFailed) {
  Write-Host ""
  Write-Host "SYMLINKS FAILED for one or more files." -ForegroundColor Yellow
  Write-Host "Enable Windows Developer Mode, then re-run this script:" -ForegroundColor Yellow
  Write-Host "  Settings > System > For developers > Developer Mode = On"
  Write-Host "  (or run this script from an elevated 'Run as administrator' PowerShell)"
}
Write-Host "Next:"
Write-Host "  - Restart your Claude Code session to pick up settings/plugins."
Write-Host "  - After editing hzb skills: claude plugin update hzb@hzb-skills"
Write-Host ""
Write-Host "WARNING: gitignored real files (credentials) live in the working tree."
Write-Host "         Do NOT run 'git clean -x' in this repo or they will be deleted."
