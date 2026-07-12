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
  $manifestPath = Join-Path $RepoRoot 'config/manifest.json'
  $externalSkillSourcesPath = Join-Path $RepoRoot 'config/external-skill-sources.json'
  $configManager = Join-Path $RepoRoot 'scripts/config.ps1'
  Assert-True (Test-Path -LiteralPath $manifestPath) 'configuration manifest exists'
  Assert-True (Test-Path -LiteralPath $externalSkillSourcesPath) 'external Dashboard skill source registry exists'
  Assert-True (Test-Path -LiteralPath $configManager) 'PowerShell configuration manager exists'
  $localDashboardServer = Join-Path $RepoRoot 'scripts/local-dashboard-server.mjs'
  Assert-True (Test-Path -LiteralPath $localDashboardServer) 'local Dashboard server exists'
  Assert-True (Test-Path -LiteralPath (Join-Path $RepoRoot 'scripts/start-local-dashboard.ps1')) 'local Dashboard PowerShell launcher exists'

  $installPs1 = Get-Content -Raw -LiteralPath (Join-Path $RepoRoot 'install.ps1')
  Assert-True ($installPs1 -match "codex\\prompts") 'install.ps1 links Codex prompt adapters'

  $manifest = Read-Json 'config/manifest.json'
  $resourceIds = @($manifest.resources | ForEach-Object { [string]$_.id })
  Assert-True ($manifest.version -eq 1) 'configuration manifest version is supported'
  Assert-True ($resourceIds.Count -gt 0) 'configuration manifest has managed resources'
  Assert-True (@($resourceIds | Group-Object | Where-Object Count -gt 1).Count -eq 0) 'configuration resource ids are unique'
  Assert-True (@($manifest.resources | Where-Object { [string]$_.target -notlike '${home}/*' }).Count -eq 0) 'managed targets stay under the selected home directory'

  $testHome = Join-Path ([System.IO.Path]::GetTempPath()) ("starrybei-config-test-" + [guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Path $testHome | Out-Null
  try {
    $planJson = & pwsh -NoProfile -File $configManager plan -HomePath $testHome -Json
    Assert-True ($LASTEXITCODE -eq 0) 'configuration plan runs against an isolated home'
    $plan = @($planJson | ConvertFrom-Json)
    Assert-True ($plan.Count -eq $resourceIds.Count) 'configuration plan covers every manifest resource'

    $null = & pwsh -NoProfile -File $configManager apply -HomePath $testHome -Json
    Assert-True ($LASTEXITCODE -eq 0) 'configuration apply succeeds against an isolated home'
    $verifyJson = & pwsh -NoProfile -File $configManager verify -HomePath $testHome -Json
    Assert-True ($LASTEXITCODE -eq 0) 'configuration verify confirms the isolated home'
    $verified = @($verifyJson | ConvertFrom-Json)
    Assert-True (@($verified | Where-Object status -ne 'installed').Count -eq 0) 'all isolated managed resources converge'

    $null = & pwsh -NoProfile -File $configManager rollback -HomePath $testHome -Json
    Assert-True ($LASTEXITCODE -eq 0) 'configuration rollback succeeds against an isolated home'
    $rolledBackJson = & pwsh -NoProfile -File $configManager plan -HomePath $testHome -Json
    $rolledBack = @($rolledBackJson | ConvertFrom-Json)
    Assert-True (@($rolledBack | Where-Object status -ne 'missing').Count -eq 0) 'rollback restores the isolated empty home'
  } finally {
    if (Test-Path -LiteralPath $testHome) {
      Remove-Item -LiteralPath $testHome -Recurse -Force
    }
  }

  $data = Read-Json 'site/data.json'
  Assert-True (-not $data.ContainsKey('mode') -or $data.mode -ne 'local') 'tracked Dashboard data stays repository-only'
  Assert-True ([int]$data.stats.total_skills -eq @($data.skills).Count) 'Dashboard skill total matches data'
  Assert-True ([int]$data.stats.total_hooks -eq @($data.hooks).Count) 'Dashboard hook total matches data'
  Assert-True ([int]$data.stats.total_configs -eq @($data.configs).Count) 'Dashboard config total matches data'
  Assert-True ([int]$data.stats.total_commands -eq @($data.commands).Count) 'Dashboard command total matches data'
  if ($data.ContainsKey('inventory')) {
    Assert-True ([int]$data.stats.total_resources -eq @($data.inventory.resources).Count) 'Dashboard resource total matches inventory data'
    $inventoryResources = @($data.inventory.resources)
    if ($inventoryResources.Count -gt 0 -and $inventoryResources[0].ContainsKey('content')) {
      foreach ($id in 'claude.settings', 'claude.instructions', 'codex.config', 'codex.prompt.checkpoint') {
        $resource = @($inventoryResources | Where-Object id -eq $id)
        Assert-True ($resource.Count -eq 1 -and -not [string]::IsNullOrWhiteSpace([string]$resource[0].content)) "Dashboard inventory includes public content for $id"
      }
    }
  }

  $localSources = @($data.skills | Where-Object {
    $_.source -eq 'local' -or [string]$_.file -like 'plugin: *'
  })
  Assert-True ($localSources.Count -eq 0) 'public Dashboard data excludes local and installed-plugin sources'

  $privateConfigs = @($data.configs | Where-Object {
    [string]$_.file -match '(?i)(\.local\.json|\.bak(?:-|$))'
  })
  Assert-True ($privateConfigs.Count -eq 0) 'public Dashboard data excludes local and backup configs'

  $externalSkillSources = Read-Json 'config/external-skill-sources.json'
  Assert-True ($externalSkillSources.version -eq 1) 'external skill source registry version is supported'
  $hzbSource = @($externalSkillSources.sources | Where-Object id -eq 'hzb')
  Assert-True ($hzbSource.Count -eq 1 -and $hzbSource[0].repository -eq 'NBStarry/hzb-skills' -and $hzbSource[0].branch -eq 'main') 'hzb Dashboard source targets the standalone repository'

  $expectedPublicHzbSkills = @(
    'codex-review',
    'conference-meeting-summary',
    'okf',
    'save-memory-before-compact',
    'web-access'
  )
  $dashboardHzbSkills = @($data.skills | Where-Object { $_.source -eq 'hzb' })
  Assert-True ($dashboardHzbSkills.Count -eq $expectedPublicHzbSkills.Count) 'Dashboard aggregates every public hzb skill'
  foreach ($skillName in $expectedPublicHzbSkills) {
    $skill = @($dashboardHzbSkills | Where-Object name -eq $skillName)
    Assert-True ($skill.Count -eq 1) "Dashboard contains public hzb skill: $skillName"
    Assert-True ($skill[0].repository -eq 'NBStarry/hzb-skills' -and $skill[0].branch -eq 'main' -and $skill[0].external -eq $true) "Dashboard records source repository for: $skillName"
  }
  Assert-True (@($data.skills | Where-Object { $_.name -in @('g1-robot', 'wlcb-dev') }).Count -eq 0) 'public Dashboard excludes private hzb overlay skills'
  Assert-True (@($data.skills | Where-Object { $_.name -eq 'karpathy-guidelines' }).Count -eq 1) 'Dashboard contains karpathy-guidelines'

  $plugins = Read-Json 'claude/configs/recommended-plugins.json'
  Assert-True (@($plugins.marketplaces).Count -eq 6) 'recommended plugin marketplace count is 6'
  Assert-True (@($plugins.plugins).Count -eq 21) 'recommended plugin count is 21'
  Assert-True (@($plugins.plugins | Where-Object { [string]$_.name -match '(?i)pua' }).Count -eq 0) 'removed pua plugins stay absent'

  & $node.Source --check $localDashboardServer
  Assert-True ($LASTEXITCODE -eq 0) 'local Dashboard server has valid JavaScript syntax'
  $localDashboardCheck = & $node.Source $localDashboardServer --check
  Write-Host $localDashboardCheck
  Assert-True ($LASTEXITCODE -eq 0) 'local Dashboard data overlay builds without external dependencies'
  Assert-True ($localDashboardCheck -match "resources=$($resourceIds.Count)" -and $localDashboardCheck -match "contents=$($resourceIds.Count)") 'local Dashboard exposes redacted content for every managed resource'
  $localDashboardSource = Get-Content -Raw -LiteralPath $localDashboardServer
  Assert-True ($localDashboardSource -notmatch 'listen\([^\r\n]*0\.0\.0\.0') 'local Dashboard does not bind to all interfaces'

  $editorSource = Get-Content -Raw -LiteralPath (Join-Path $RepoRoot 'site/js/editor.js')
  Assert-True ($editorSource -notmatch '(sessionStorage|github_token|api\.github\.com|Authorization)') 'Dashboard editor does not handle GitHub tokens'
  Assert-True ($editorSource -match '/edit/' -and $editorSource -match '/new/' -and $editorSource -match '/delete/') 'Dashboard editor delegates mutations to GitHub-native pages'
  Assert-True ($editorSource -match 'repository' -and $editorSource -match 'branch') 'Dashboard editor supports per-skill source repositories'

  $sensitiveTrackedPaths = @(
    'claude/configs/settings.local.json',
    'claude/configs/settings.glm.json',
    'claude/configs/settings.windows.local.json'
  )
  foreach ($path in $sensitiveTrackedPaths) {
    Assert-True ($trackedFiles -notcontains $path) "sensitive local file is not tracked: $path"
  }
  Assert-True (@($trackedFiles | Where-Object { $_ -like 'skills/hzb-skills/*' }).Count -eq 0) 'external hzb-skills source is not vendored'

  Write-Host "All $script:CheckCount automated repository checks passed."
} finally {
  Pop-Location
}
