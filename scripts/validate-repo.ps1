[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$script:CheckCount = 0

function Assert-True([bool]$Condition, [string]$Message) {
  $script:CheckCount++
  if (-not $Condition) {
    throw "[FAIL] $Message"
  }
  Write-Host "[PASS] $Message"
}

function Read-Json([string]$RelativePath) {
  $path = Join-Path $RepoRoot $RelativePath
  try {
    return Get-Content -Raw -LiteralPath $path | ConvertFrom-Json -AsHashtable
  } catch {
    throw "Invalid JSON: $RelativePath`n$($_.Exception.Message)"
  }
}

Push-Location $RepoRoot
try {
  $trackedFiles = @(& git ls-files)
  Assert-True ($LASTEXITCODE -eq 0) 'git can enumerate tracked files'

  $jsonFiles = @($trackedFiles | Where-Object { $_ -like '*.json' })
  foreach ($file in $jsonFiles) {
    $null = Read-Json $file
  }
  Assert-True ($jsonFiles.Count -gt 0) "all $($jsonFiles.Count) tracked JSON files parse"

  $powerShellFiles = @($trackedFiles | Where-Object { $_ -like '*.ps1' })
  foreach ($file in $powerShellFiles) {
    $tokens = $null
    $errors = $null
    $null = [System.Management.Automation.Language.Parser]::ParseFile(
      (Join-Path $RepoRoot $file),
      [ref]$tokens,
      [ref]$errors
    )
    Assert-True (@($errors).Count -eq 0) "$file has valid PowerShell syntax"
  }

  $node = Get-Command node -ErrorAction SilentlyContinue
  Assert-True ($null -ne $node) 'node is available for JavaScript syntax checks'
  $javaScriptFiles = @($trackedFiles | Where-Object { $_ -like 'site/js/*.js' })
  foreach ($file in $javaScriptFiles) {
    & $node.Source --check (Join-Path $RepoRoot $file)
    Assert-True ($LASTEXITCODE -eq 0) "$file has valid JavaScript syntax"
  }

  Assert-True (Test-Path -LiteralPath (Join-Path $RepoRoot 'AGENTS.md')) 'AGENTS.md exists'
  Assert-True (-not (Test-Path -LiteralPath (Join-Path $RepoRoot 'CLAUDE.md'))) 'root CLAUDE.md is removed'
  Assert-True (Test-Path -LiteralPath (Join-Path $RepoRoot 'codex/prompts/checkpoint.md')) 'checkpoint prompt adapter exists'

  $installPs1 = Get-Content -Raw -LiteralPath (Join-Path $RepoRoot 'install.ps1')
  Assert-True ($installPs1 -match "codex\\prompts") 'install.ps1 links Codex prompt adapters'

  $data = Read-Json 'site/data.json'
  Assert-True ([int]$data.stats.total_skills -eq @($data.skills).Count) 'Dashboard skill total matches data'
  Assert-True ([int]$data.stats.total_hooks -eq @($data.hooks).Count) 'Dashboard hook total matches data'
  Assert-True ([int]$data.stats.total_configs -eq @($data.configs).Count) 'Dashboard config total matches data'
  Assert-True ([int]$data.stats.total_commands -eq @($data.commands).Count) 'Dashboard command total matches data'

  $localSources = @($data.skills | Where-Object {
    $_.source -eq 'local' -or [string]$_.file -like 'plugin: *'
  })
  Assert-True ($localSources.Count -eq 0) 'public Dashboard data excludes local and installed-plugin sources'

  $privateConfigs = @($data.configs | Where-Object {
    [string]$_.file -match '(?i)(\.local\.json|\.bak(?:-|$))'
  })
  Assert-True ($privateConfigs.Count -eq 0) 'public Dashboard data excludes local and backup configs'

  $expectedHzbSkills = @(
    'codex-review',
    'conference-meeting-summary',
    'g1-robot',
    'okf',
    'save-memory-before-compact',
    'web-access',
    'wlcb-dev'
  )
  $hzbNames = @($data.skills | Where-Object { $_.source -eq 'hzb' } | ForEach-Object { $_.name })
  foreach ($name in $expectedHzbSkills) {
    Assert-True ($hzbNames -contains $name) "Dashboard contains hzb skill: $name"
  }
  Assert-True (@($data.skills | Where-Object { $_.name -eq 'karpathy-guidelines' }).Count -eq 1) 'Dashboard contains karpathy-guidelines'

  $plugins = Read-Json 'claude/configs/recommended-plugins.json'
  Assert-True (@($plugins.marketplaces).Count -eq 6) 'recommended plugin marketplace count is 6'
  Assert-True (@($plugins.plugins).Count -eq 21) 'recommended plugin count is 21'
  Assert-True (@($plugins.plugins | Where-Object { [string]$_.name -match '(?i)pua' }).Count -eq 0) 'removed pua plugins stay absent'

  $sensitiveTrackedPaths = @(
    'claude/configs/settings.local.json',
    'claude/configs/settings.glm.json',
    'claude/configs/settings.windows.local.json',
    'skills/hzb-skills/plugins/hzb/commands/connect-internal.md',
    'skills/hzb-skills/plugins/hzb/commands/connect-internal-backup.md',
    'skills/hzb-skills/plugins/hzb/skills/g1-robot/SKILL.md',
    'skills/hzb-skills/plugins/hzb/skills/wlcb-dev/SKILL.md'
  )
  foreach ($path in $sensitiveTrackedPaths) {
    Assert-True ($trackedFiles -notcontains $path) "sensitive local file is not tracked: $path"
  }

  Write-Host "All $script:CheckCount automated repository checks passed."
} finally {
  Pop-Location
}
