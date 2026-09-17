# ====================================================================
# ShopSense - Milestone 4 Weekly AI Agent Workflow Runner
# ====================================================================

[CmdletBinding()]
param(
    [string]$Email,
    [switch]$All
)

$ErrorActionPreference = "Continue"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   ShopSense - Weekly AI Agent Workflow Runner (LangGraph)" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

# 1. Detect Python environment
$pythonCandidates = @(
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
    "C:\Users\vasanthkumar\AppData\Local\Programs\Python\Python313\python.exe",
    (Join-Path $projectRoot ".venv\Scripts\python.exe"),
    (Join-Path $projectRoot "venv\Scripts\python.exe"),
    (Join-Path $projectRoot "env\Scripts\python.exe")
)

$dynamicAppData = Get-Item "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
if ($dynamicAppData) { $pythonCandidates += $dynamicAppData }

$pathPython = Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue
if ($pathPython -and $pathPython -notlike "*WindowsApps*") { $pythonCandidates += $pathPython }

$pythonExe = $null
foreach ($cand in $pythonCandidates) {
    if (-not $cand) { continue }
    if ($cand -like "*WindowsApps*") { continue }
    if (-not (Test-Path $cand)) { continue }
    try {
        $testVer = & $cand --version 2>&1
        $testVerStr = ($testVer | Out-String).Trim()
        if ($testVerStr -match "^Python\s+3\.\d+" -and $testVerStr -notmatch "not found") {
            $pythonExe = $cand
            break
        }
    } catch {}
}

if (-not $pythonExe) {
    Write-Host "[ERROR] Could not locate working Python 3.11+ executable." -ForegroundColor Red
    exit 1
}

$pyDir = Split-Path -Parent $pythonExe
$scriptsDir = Join-Path $pyDir "Scripts"
if ($env:PATH -notlike "*$pyDir*") {
    $env:PATH = "$pyDir;$scriptsDir;$env:PATH"
}

Write-Host "Using Python: $pythonExe" -ForegroundColor Green

# 2. Run the weekly agent workflow
$cliArgs = @("run_weekly_agent.py")
if ($Email) {
    $cliArgs += "--email"
    $cliArgs += $Email
} elseif ($All) {
    $cliArgs += "--all"
}

Write-Host "Executing LangGraph AI Agent Workflow against MySQL..." -ForegroundColor Yellow
& $pythonExe $cliArgs

$exitCode = $LASTEXITCODE
if ($exitCode -eq 0) {
    Write-Host "`n[SUCCESS] Weekly AI Agent Workflow completed successfully!" -ForegroundColor Green
} else {
    Write-Host "`n[ERROR] Weekly AI Agent Workflow encountered errors (Exit Code: $exitCode)." -ForegroundColor Red
}

exit $exitCode
