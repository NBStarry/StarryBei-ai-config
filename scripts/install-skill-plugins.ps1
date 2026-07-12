[CmdletBinding()]
param(
  [switch]$Plan
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ManifestPath = Join-Path $RepoRoot 'config/skill-plugins.json'
$Manifest = Get-Content -Raw -LiteralPath $ManifestPath | ConvertFrom-Json

function Format-Command([string]$Command, [string[]]$Arguments) {
  return (($Command) + ' ' + ($Arguments -join ' ')).Trim()
}

function Invoke-Checked([string]$Command, [string[]]$Arguments) {
  & $Command @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "Command failed ($LASTEXITCODE): $(Format-Command $Command $Arguments)"
  }
}

function Invoke-Json([string]$Command, [string[]]$Arguments) {
  $output = @(& $Command @Arguments)
  if ($LASTEXITCODE -ne 0) {
    throw "Command failed ($LASTEXITCODE): $(Format-Command $Command $Arguments)"
  }
  return (($output -join "`n") | ConvertFrom-Json)
}

function Get-MarketplaceArguments([string]$Tool, $Marketplace) {
  if ($Tool -eq 'claude') {
    return @('plugin', 'marketplace', 'add', [string]$Marketplace.repository)
  }
  return @('plugin', 'marketplace', 'add', [string]$Marketplace.repository, '--ref', [string]$Marketplace.branch, '--json')
}

function Get-PluginArguments([string]$Tool, $Plugin) {
  $selector = "$($Plugin.name)@$($Plugin.marketplace)"
  if ($Tool -eq 'claude') {
    return @('plugin', 'install', $selector, '--scope', 'user')
  }
  return @('plugin', 'add', $selector, '--json')
}

foreach ($tool in @('claude', 'codex')) {
  $marketplaces = @($Manifest.marketplaces | Where-Object { $_.tools -contains $tool })
  $plugins = @($Manifest.plugins | Where-Object { $_.tools -contains $tool })

  if ($Plan) {
    foreach ($marketplace in $marketplaces) {
      Write-Output (Format-Command $tool (Get-MarketplaceArguments $tool $marketplace))
    }
    foreach ($plugin in $plugins) {
      Write-Output (Format-Command $tool (Get-PluginArguments $tool $plugin))
    }
    continue
  }

  if ($null -eq (Get-Command $tool -ErrorAction SilentlyContinue)) {
    Write-Warning "$tool is not installed; skipping its skill plugins."
    continue
  }

  if ($tool -eq 'claude') {
    $marketplaceState = @(Invoke-Json $tool @('plugin', 'marketplace', 'list', '--json'))
    $existingMarketplaces = @($marketplaceState | ForEach-Object { [string]$_.name })
  } else {
    $marketplaceState = Invoke-Json $tool @('plugin', 'marketplace', 'list', '--json')
    $existingMarketplaces = @($marketplaceState.marketplaces | ForEach-Object { [string]$_.name })
  }

  foreach ($marketplace in $marketplaces) {
    if ($existingMarketplaces -contains [string]$marketplace.id) {
      Write-Host "present  $tool marketplace $($marketplace.id)"
      continue
    }
    Write-Host "adding   $tool marketplace $($marketplace.id)"
    Invoke-Checked $tool (Get-MarketplaceArguments $tool $marketplace)
  }

  if ($tool -eq 'claude') {
    $pluginState = @(Invoke-Json $tool @('plugin', 'list', '--json'))
    $installedPlugins = @($pluginState | ForEach-Object { [string]$_.id })
  } else {
    $pluginState = Invoke-Json $tool @('plugin', 'list', '--json')
    $installedPlugins = @($pluginState.installed | ForEach-Object { [string]$_.pluginId })
  }

  foreach ($plugin in $plugins) {
    $selector = "$($plugin.name)@$($plugin.marketplace)"
    if ($installedPlugins -contains $selector) {
      Write-Host "present  $tool plugin $selector"
      continue
    }
    Write-Host "install  $tool plugin $selector"
    Invoke-Checked $tool (Get-PluginArguments $tool $plugin)
  }
}
