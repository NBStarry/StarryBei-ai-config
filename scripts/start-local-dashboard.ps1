[CmdletBinding()]
param(
  [ValidateRange(1024, 65535)]
  [int]$Port = 4173,
  [switch]$NoBrowser
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$node = Get-Command node -ErrorAction SilentlyContinue
if ($null -eq $node) {
  throw 'Node.js is required. Install an active LTS release and retry.'
}

$server = Join-Path $PSScriptRoot 'local-dashboard-server.mjs'
$arguments = @($server, '--port', [string]$Port)
if (-not $NoBrowser) {
  $arguments += '--open'
}

Write-Host 'Building an in-memory local Dashboard snapshot...'
Write-Host 'Authentication files are excluded and sensitive values are redacted.'
& $node.Source @arguments
