# Windows port of statusline.sh — no `jq` dependency, uses native ConvertFrom-Json.
# Renders: ◆session · path · model · branch · ctx%
# Context % is colored: green <50 / yellow 50-80 / red >=80.
# Wire up in settings via:
#   powershell -NoProfile -ExecutionPolicy Bypass -File <HOME>/.claude/statusline.ps1
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding  = [System.Text.Encoding]::UTF8

# Read stdin as raw UTF-8 bytes. PowerShell 5.1 would otherwise decode the piped
# JSON with the OEM code page (GBK here) before the script runs, mangling any
# non-ASCII content (e.g. a Chinese session name).
$stdinStream = [System.Console]::OpenStandardInput()
$reader = New-Object System.IO.StreamReader($stdinStream, [System.Text.Encoding]::UTF8)
$raw = $reader.ReadToEnd()
$reader.Dispose()
if (-not $raw) { return }
$j = $raw | ConvertFrom-Json

# Build non-ASCII glyphs from code points, not source literals: PowerShell 5.1
# reads BOM-less .ps1 files as the system ANSI code page, which would mangle them.
$esc     = [char]27
$diamond = [char]0x25C6   # ◆
$sep     = ' ' + [char]0x00B7 + ' '   # " · "
function Color([string]$text, [string]$code) { "$esc[$code" + "m$text$esc[0m" }

$currentDir = if ($j.workspace.current_dir) { $j.workspace.current_dir } else { (Get-Location).Path }

# ---- Session name (from /rename or auto) → basename of cwd fallback ----
$sn = if ($j.session_name) { $j.session_name } else { Split-Path -Leaf $currentDir }

# ---- Short path: ~ for home, keep first 2 + last 2 segments ----
$homeDir = $env:USERPROFILE
$short = $currentDir
if ($homeDir -and $short.StartsWith($homeDir, [System.StringComparison]::OrdinalIgnoreCase)) {
    $short = '~' + $short.Substring($homeDir.Length)
}
$short = $short -replace '\\', '/'
$parts = $short -split '/' | Where-Object { $_ -ne '' }
if ($parts.Count -gt 5) {
    $short = "$($parts[0])/$($parts[1])/…/$($parts[-2])/$($parts[-1])"
}

# ---- Model: "X.Y (1M context)" → "X.Y·1M" ----
$model = $j.model.display_name
if ($model) { $model = $model -replace ' ?\((?:with )?1M context\)', ([char]0x00B7 + '1M') }

# ---- Git branch (only inside a repo) ----
$branch = ''
try {
    $b = git --no-optional-locks -C $currentDir branch --show-current 2>$null
    if ($LASTEXITCODE -eq 0 -and $b) { $branch = $b.Trim() }
} catch {}

# ---- Context % ----
$ctx = ''
$rem = $j.context_window.remaining_percentage
if ($null -ne $rem -and $rem -ne '') {
    $used = [math]::Round(100 - $rem)
    $code = if ($used -lt 50) { '1;32' } elseif ($used -lt 80) { '1;33' } else { '1;31' }
    $ctx = Color "$used%" $code
}

# ---- Assemble: ◆session · path · model · branch · ctx% ----
$out = Color "$diamond$sn" '1;35'
if ($short)  { $out += $sep + (Color $short  '1;34') }
if ($model)  { $out += $sep + (Color $model  '1;36') }
if ($branch) { $out += $sep + (Color $branch '1;33') }
if ($ctx)    { $out += $sep + $ctx }

# Emit raw UTF-8 bytes directly — bypasses console/redirection codepage so the
# ◆ · glyphs and ANSI colors survive regardless of the active code page.
$bytes  = [System.Text.Encoding]::UTF8.GetBytes($out)
$stdout = [System.Console]::OpenStandardOutput()
$stdout.Write($bytes, 0, $bytes.Length)
$stdout.Flush()
