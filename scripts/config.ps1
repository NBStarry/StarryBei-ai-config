[CmdletBinding()]
param(
  [Parameter(Position = 0)]
  [ValidateSet('doctor', 'plan', 'apply', 'verify', 'rollback')]
  [string]$Command = 'plan',

  [string]$HomePath = $HOME,
  [string]$ManifestPath,
  [string]$Transaction,
  [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $ManifestPath) {
  $ManifestPath = Join-Path $RepoRoot 'config/manifest.json'
}
$HomePath = [System.IO.Path]::GetFullPath($HomePath)
$StateRoot = Join-Path $HomePath '.starrybei-ai-config'
$TransactionsRoot = Join-Path $StateRoot 'transactions'
$BackupsRoot = Join-Path $StateRoot 'backups'

function Get-CurrentPlatform {
  if ($IsWindows) { return 'windows' }
  if ($IsMacOS) { return 'macos' }
  return 'linux'
}

function Test-ToolAvailable([string]$Name) {
  if ($null -ne (Get-Command $Name -ErrorAction SilentlyContinue)) { return $true }

  if ($Name -eq 'codex' -and $IsWindows -and -not [string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    $codexBin = Join-Path $env:LOCALAPPDATA 'OpenAI\Codex\bin'
    if (Test-Path -LiteralPath $codexBin) {
      return $null -ne (Get-ChildItem -LiteralPath $codexBin -Recurse -Filter 'codex.exe' -ErrorAction SilentlyContinue | Select-Object -First 1)
    }
  }

  return $false
}

function Get-OptionalProperty([object]$Value, [string]$Name) {
  $property = $Value.PSObject.Properties[$Name]
  if ($null -eq $property) { return $null }
  return $property.Value
}

function Read-Manifest {
  if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    throw "Manifest not found: $ManifestPath"
  }
  try {
    $manifest = Get-Content -Raw -LiteralPath $ManifestPath | ConvertFrom-Json
  } catch {
    throw "Invalid manifest JSON: $($_.Exception.Message)"
  }
  if ($manifest.version -ne 1) {
    throw "Unsupported manifest version: $($manifest.version)"
  }
  $ids = @($manifest.resources | ForEach-Object { $_.id })
  if (@($ids | Group-Object | Where-Object Count -gt 1).Count -gt 0) {
    throw 'Manifest resource ids must be unique.'
  }
  return $manifest
}

function Expand-Target([string]$Template) {
  $normalized = $Template.Replace('${home}', $HomePath).Replace('/', [System.IO.Path]::DirectorySeparatorChar)
  return [System.IO.Path]::GetFullPath($normalized)
}

function Resolve-ResourceSource([object]$Resource) {
  $candidates = @()
  $source = Get-OptionalProperty $Resource 'source'
  if ($source) { $candidates += [string]$source }
  $sourceCandidates = Get-OptionalProperty $Resource 'sourceCandidates'
  if ($sourceCandidates) { $candidates += @($sourceCandidates | ForEach-Object { [string]$_ }) }

  foreach ($candidate in $candidates) {
    $path = if ([System.IO.Path]::IsPathRooted($candidate)) {
      $candidate
    } else {
      Join-Path $RepoRoot $candidate
    }
    if (Test-Path -LiteralPath $path) {
      return [System.IO.Path]::GetFullPath($path)
    }
  }
  return $null
}

function Get-PathEntry([string]$Path) {
  $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
  if ($null -ne $item) { return $item }

  $parent = Split-Path -Parent $Path
  $name = Split-Path -Leaf $Path
  if (-not (Test-Path -LiteralPath $parent -PathType Container)) { return $null }
  return Get-ChildItem -LiteralPath $parent -Force -ErrorAction SilentlyContinue |
    Where-Object Name -eq $name |
    Select-Object -First 1
}

function Get-NormalizedPath([string]$Path, [string]$BasePath) {
  if (-not [System.IO.Path]::IsPathRooted($Path)) {
    $Path = Join-Path $BasePath $Path
  }
  $full = [System.IO.Path]::GetFullPath($Path).TrimEnd('\', '/')
  if ($IsWindows) { return $full.ToLowerInvariant() }
  return $full
}

function Test-LinkTarget([object]$Item, [string]$ExpectedSource) {
  $linkType = [string](Get-OptionalProperty $Item 'LinkType')
  if (-not $linkType) { return $false }
  $targets = @(Get-OptionalProperty $Item 'Target')
  if ($targets.Count -eq 0 -or -not $targets[0]) { return $false }
  $itemParent = Split-Path -Parent ([string]$Item.FullName)
  $actual = Get-NormalizedPath ([string]$targets[0]) $itemParent
  $expected = Get-NormalizedPath $ExpectedSource $RepoRoot
  return $actual -eq $expected
}

function Get-ResourceState([object]$Resource) {
  $platform = Get-CurrentPlatform
  $supported = @($Resource.platforms) -contains $platform
  $toolAvailable = Test-ToolAvailable ([string]$Resource.tool)
  $target = Expand-Target ([string]$Resource.target)
  $source = Resolve-ResourceSource $Resource
  $item = Get-PathEntry $target

  $status = 'missing'
  $detail = 'Target does not exist.'
  if (-not $supported) {
    $status = 'unsupported'
    $detail = "Not managed on $platform."
  } elseif (-not $toolAvailable) {
    $status = 'tool-not-installed'
    $detail = "$($Resource.tool) is not installed; resource is not managed on this machine."
  } elseif (-not $source) {
    $status = 'missing-source'
    $detail = 'No source candidate exists in this checkout.'
  } elseif ($Resource.method -eq 'seed') {
    if ($null -ne $item) {
      $status = 'installed'
      $detail = 'Seed target exists and is intentionally not overwritten.'
    }
  } elseif ($null -ne $item) {
    if (Test-LinkTarget $item $source) {
      $status = 'installed'
      $detail = 'Target points to the selected repository source.'
    } else {
      $status = 'drifted'
      $detail = 'Target exists but does not point to the selected repository source.'
    }
  }

  $action = switch ($status) {
    'missing' { 'install' }
    'drifted' { 'replace' }
    default { 'none' }
  }

  [pscustomobject]@{
    id = [string]$Resource.id
    tool = [string]$Resource.tool
    kind = [string]$Resource.kind
    method = [string]$Resource.method
    status = $status
    action = $action
    source = $source
    target = $target
    description = [string]$Resource.description
    detail = $detail
  }
}

function Get-Plan {
  $manifest = Read-Manifest
  return @($manifest.resources | ForEach-Object { Get-ResourceState $_ })
}

function Write-StateTable([object[]]$States) {
  $States | Format-Table -AutoSize id, tool, kind, method, status, action
  $counts = $States | Group-Object status | Sort-Object Name
  Write-Host ''
  Write-Host (($counts | ForEach-Object { "$($_.Name)=$($_.Count)" }) -join '  ')
}

function Invoke-Doctor {
  $checks = @(
    [pscustomobject]@{ check = 'PowerShell'; ok = $PSVersionTable.PSVersion.Major -ge 7; detail = $PSVersionTable.PSVersion.ToString() },
    [pscustomobject]@{ check = 'Manifest'; ok = Test-Path -LiteralPath $ManifestPath -PathType Leaf; detail = $ManifestPath },
    [pscustomobject]@{ check = 'Repository'; ok = Test-Path -LiteralPath (Join-Path $RepoRoot '.git'); detail = $RepoRoot },
    [pscustomobject]@{ check = 'Home'; ok = Test-Path -LiteralPath $HomePath -PathType Container; detail = $HomePath },
    [pscustomobject]@{ check = 'Git'; ok = $null -ne (Get-Command git -ErrorAction SilentlyContinue); detail = 'Required for normal repository workflows' },
    [pscustomobject]@{ check = 'Node'; ok = $null -ne (Get-Command node -ErrorAction SilentlyContinue); detail = 'Required for the local Dashboard' }
  )
  $null = Read-Manifest
  if ($Json) {
    $checks | ConvertTo-Json -Depth 4
  } else {
    $checks | Format-Table -AutoSize
  }
  if (@($checks | Where-Object { -not $_.ok }).Count -gt 0) {
    throw 'One or more doctor checks failed.'
  }
}

function New-ManagedTarget([object]$State) {
  $parent = Split-Path -Parent $State.target
  $null = New-Item -ItemType Directory -Path $parent -Force
  switch ($State.method) {
    'seed' {
      Copy-Item -LiteralPath $State.source -Destination $State.target
    }
    'junction' {
      $null = New-Item -ItemType Junction -Path $State.target -Target $State.source
    }
    'symlink' {
      $null = New-Item -ItemType SymbolicLink -Path $State.target -Target $State.source
    }
    default {
      throw "Unsupported install method: $($State.method)"
    }
  }
}

function Invoke-Apply {
  $states = Get-Plan
  $changes = @($states | Where-Object { $_.action -ne 'none' })
  if ($changes.Count -eq 0) {
    if ($Json) { '[]' } else { Write-Host 'Already converged; no changes required.' }
    return
  }

  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
  $backupRoot = Join-Path $BackupsRoot $stamp
  $journalPath = Join-Path $TransactionsRoot "$stamp.json"
  $entries = @()
  $null = New-Item -ItemType Directory -Path $backupRoot -Force
  $null = New-Item -ItemType Directory -Path $TransactionsRoot -Force

  try {
    foreach ($state in $changes) {
      $item = Get-PathEntry $state.target
      $backupPath = Join-Path $backupRoot $state.id
      $hadTarget = $null -ne $item
      if ($hadTarget) {
        Move-Item -LiteralPath $state.target -Destination $backupPath
      }
      try {
        New-ManagedTarget $state
      } catch {
        if (Get-PathEntry $state.target) {
          Remove-Item -LiteralPath $state.target -Force
        }
        if ($hadTarget -and (Get-PathEntry $backupPath)) {
          Move-Item -LiteralPath $backupPath -Destination $state.target
        }
        throw
      }
      $entries += [pscustomobject]@{
        id = $state.id
        target = $state.target
        source = $state.source
        method = $state.method
        hadTarget = $hadTarget
        backupPath = if ($hadTarget) { $backupPath } else { $null }
      }
    }

    $journal = [ordered]@{
      version = 1
      id = $stamp
      createdAt = (Get-Date).ToUniversalTime().ToString('o')
      repoRoot = $RepoRoot
      homePath = $HomePath
      state = 'applied'
      entries = $entries
    }
    $journal | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $journalPath -Encoding utf8
  } catch {
    $completed = @($entries)
    [array]::Reverse($completed)
    foreach ($entry in $completed) {
      if (Get-PathEntry ([string]$entry.target)) {
        Remove-Item -LiteralPath ([string]$entry.target) -Force
      }
      if ($entry.hadTarget -and $entry.backupPath -and (Get-PathEntry ([string]$entry.backupPath))) {
        $null = New-Item -ItemType Directory -Path (Split-Path -Parent ([string]$entry.target)) -Force
        Move-Item -LiteralPath ([string]$entry.backupPath) -Destination ([string]$entry.target)
      }
    }
    Write-Error "Apply stopped: $($_.Exception.Message)"
    throw
  }

  if ($Json) {
    $entries | ConvertTo-Json -Depth 5
  } else {
    Write-Host "Applied $($entries.Count) change(s)."
    Write-Host "Transaction: $stamp"
    Write-Host "Journal: $journalPath"
  }
}

function Resolve-TransactionPath {
  if ($Transaction) {
    if (Test-Path -LiteralPath $Transaction -PathType Leaf) {
      return [System.IO.Path]::GetFullPath($Transaction)
    }
    $candidate = Join-Path $TransactionsRoot "$Transaction.json"
    if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
    throw "Transaction not found: $Transaction"
  }
  $latest = Get-ChildItem -LiteralPath $TransactionsRoot -Filter '*.json' -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTimeUtc -Descending |
    Select-Object -First 1
  if ($null -eq $latest) { throw 'No transaction is available to roll back.' }
  return $latest.FullName
}

function Invoke-Rollback {
  $journalPath = Resolve-TransactionPath
  $journal = Get-Content -Raw -LiteralPath $journalPath | ConvertFrom-Json
  if ($journal.state -eq 'rolled-back') {
    throw "Transaction is already rolled back: $($journal.id)"
  }

  $entries = @($journal.entries)
  [array]::Reverse($entries)
  foreach ($entry in $entries) {
    if (Get-PathEntry ([string]$entry.target)) {
      Remove-Item -LiteralPath ([string]$entry.target) -Force
    }
    if ($entry.hadTarget -and $entry.backupPath -and (Get-PathEntry ([string]$entry.backupPath))) {
      $null = New-Item -ItemType Directory -Path (Split-Path -Parent ([string]$entry.target)) -Force
      Move-Item -LiteralPath ([string]$entry.backupPath) -Destination ([string]$entry.target)
    }
  }
  $journal.state = 'rolled-back'
  $journal | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $journalPath -Encoding utf8
  if ($Json) { $journal | ConvertTo-Json -Depth 6 } else { Write-Host "Rolled back transaction $($journal.id)." }
}

switch ($Command) {
  'doctor' { Invoke-Doctor }
  'plan' {
    $states = Get-Plan
    if ($Json) { $states | ConvertTo-Json -Depth 5 } else { Write-StateTable $states }
  }
  'apply' { Invoke-Apply }
  'verify' {
    $states = Get-Plan
    if ($Json) { $states | ConvertTo-Json -Depth 5 } else { Write-StateTable $states }
    $problems = @($states | Where-Object { $_.status -notin @('installed', 'unsupported', 'tool-not-installed') })
    if ($problems.Count -gt 0) { throw "$($problems.Count) managed resource(s) are not converged." }
  }
  'rollback' { Invoke-Rollback }
}
