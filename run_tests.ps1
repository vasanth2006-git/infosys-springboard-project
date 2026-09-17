# ====================================================================
# ShopSense Marketplace - Milestone 4 Automated Unit Test Runner
# ====================================================================

[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   ShopSense Marketplace - Milestone 4 Unit Test Runner " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# Set execution directory to project root
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

# --------------------------------------------------------------------
# 1. Locate the Project Python Executable
# --------------------------------------------------------------------
Write-Host "`n[1/4] Detecting Python environment..." -ForegroundColor Yellow

$pythonCandidates = @(
    # Check the existing Python 3.13 installation where ShopSense packages reside (highest priority)
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
    "C:\Users\vasanthkumar\AppData\Local\Programs\Python\Python313\python.exe",
    (Join-Path $projectRoot ".venv\Scripts\python.exe"),
    (Join-Path $projectRoot "venv\Scripts\python.exe"),
    (Join-Path $projectRoot "env\Scripts\python.exe")
)

# Also check dynamic wildcard paths in AppData and Program Files
$dynamicAppData = Get-Item "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
if ($dynamicAppData) { $pythonCandidates += $dynamicAppData }

$dynamicProgFiles = Get-Item "C:\Program Files\Python*\python.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
if ($dynamicProgFiles) { $pythonCandidates += $dynamicProgFiles }

# Add Python Launcher if present
$pyLauncher = "$env:LOCALAPPDATA\Programs\Python\Launcher\py.exe"
if (Test-Path $pyLauncher) { $pythonCandidates += $pyLauncher }

# PATH candidates (explicitly excluding Microsoft Store WindowsApps stubs)
$pathPython = Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue
if ($pathPython -and $pathPython -notlike "*WindowsApps*") { $pythonCandidates += $pathPython }

$pathPy = Get-Command py -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue
if ($pathPy -and $pathPy -notlike "*WindowsApps*") { $pythonCandidates += $pathPy }

$pythonExe = $null

foreach ($cand in $pythonCandidates) {
    if (-not $cand) { continue }
    # Ignore WindowsApps dummy stubs which output "Python was not found"
    if ($cand -like "*WindowsApps*") { continue }
    if (-not (Test-Path $cand)) { continue }

    try {
        $testVer = & $cand --version 2>&1
        $testVerStr = ($testVer | Out-String).Trim()
        if ($testVerStr -match "^Python\s+3\.\d+" -and $testVerStr -notmatch "not found") {
            $sysExec = & $cand -c "import sys; print(sys.executable)" 2>&1
            $sysExecStr = ($sysExec | Out-String).Trim()
            if ($LASTEXITCODE -eq 0 -and $sysExecStr -notmatch "not found") {
                $pythonExe = $cand
                break
            }
        }
    } catch {
        # continue checking candidates
    }
}

if (-not $pythonExe) {
    Write-Host "`n[ERROR] Could not locate a working Python executable." -ForegroundColor Red
    Write-Host "Please ensure Python 3.11+ is installed on this machine." -ForegroundColor Red
    exit 1
}

# Update session PATH with Python and Scripts folders for convenience
$pyDir = Split-Path -Parent $pythonExe
$scriptsDir = Join-Path $pyDir "Scripts"
if ($env:PATH -notlike "*$pyDir*") {
    $env:PATH = "$pyDir;$scriptsDir;$env:PATH"
}

$pyVersionStr = (& $pythonExe --version 2>&1).ToString().Trim()
Write-Host "      Detected Python: $pythonExe ($pyVersionStr)" -ForegroundColor Green

# --------------------------------------------------------------------
# 2. Check and Install Missing Test Dependencies (pytest, httpx)
# --------------------------------------------------------------------
Write-Host "`n[2/4] Checking testing dependencies (pytest & httpx)..." -ForegroundColor Yellow

$needsInstall = $false
try {
    $checkOut = & $pythonExe -c "import pytest; import httpx; print('READY')" 2>&1
    if ($checkOut -notmatch "READY") {
        $needsInstall = $true
    }
} catch {
    $needsInstall = $true
}

if ($needsInstall) {
    Write-Host "      Missing testing dependencies detected. Installing pytest and httpx..." -ForegroundColor Cyan
    & $pythonExe -m pip install --quiet pytest httpx
    if ($LASTEXITCODE -ne 0) {
        Write-Host "      Retrying installation from requirements.txt..." -ForegroundColor Yellow
        & $pythonExe -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            Write-Host "`n[ERROR] Failed to install pytest/httpx into $pythonExe" -ForegroundColor Red
            exit 1
        }
    }
    Write-Host "      Testing dependencies installed successfully!" -ForegroundColor Green
} else {
    $pytestVer = & $pythonExe -m pytest --version 2>&1
    Write-Host "      Dependencies satisfied: $pytestVer" -ForegroundColor Green
}

# --------------------------------------------------------------------
# 3. Execute Pytest Test Suite
# --------------------------------------------------------------------
Write-Host "`n[3/4] Running ShopSense automated unit test suite..." -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan

$testLines = @()
& $pythonExe -m pytest tests -v --tb=short 2>&1 | ForEach-Object {
    $line = $_.ToString()
    $testLines += $line

    # Colorize real-time test execution output
    if ($line -match "PASSED") {
        Write-Host $line -ForegroundColor Green
    } elseif ($line -match "FAILED") {
        Write-Host $line -ForegroundColor Red
    } elseif ($line -match "ERROR") {
        Write-Host $line -ForegroundColor Red
    } elseif ($line -match "SKIPPED") {
        Write-Host $line -ForegroundColor Yellow
    } else {
        Write-Host $line -ForegroundColor Gray
    }
}

$testExitCode = $LASTEXITCODE

# --------------------------------------------------------------------
# 4. Parse Results & Print Unambiguous Summary
# --------------------------------------------------------------------
Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host "                TEST EXECUTION SUMMARY                  " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$passedCount = 0
$failedCount = 0
$errorCount = 0
$skippedCount = 0

# Count each individual test result line
foreach ($line in $testLines) {
    if ($line -match "::\S+\s+PASSED") {
        $passedCount++
    } elseif ($line -match "::\S+\s+FAILED") {
        $failedCount++
    } elseif ($line -match "::\S+\s+ERROR") {
        $errorCount++
    } elseif ($line -match "::\S+\s+SKIPPED") {
        $skippedCount++
    }
}

# Also verify with the pytest summary line
$summaryLine = $testLines | Where-Object { $_ -match "=+\s+.*(passed|failed).*\s+=+" } | Select-Object -Last 1
if ($summaryLine) {
    if ($summaryLine -match "(\d+)\s+passed") { $passedCount = [int]$matches[1] }
    if ($summaryLine -match "(\d+)\s+failed") { $failedCount = [int]$matches[1] }
    if ($summaryLine -match "(\d+)\s+error") { $errorCount = [int]$matches[1] }
    if ($summaryLine -match "(\d+)\s+skipped") { $skippedCount = [int]$matches[1] }
}

$totalTests = $passedCount + $failedCount + $errorCount + $skippedCount

Write-Host "  Python Binary  : $pythonExe" -ForegroundColor White
Write-Host "  Test Directory : $projectRoot\tests" -ForegroundColor White
Write-Host "  Total Tests    : $totalTests" -ForegroundColor White
Write-Host "  PASSED Tests   : $passedCount" -ForegroundColor Green

if ($failedCount -gt 0) {
    Write-Host "  FAILED Tests   : $failedCount" -ForegroundColor Red
} else {
    Write-Host "  FAILED Tests   : 0" -ForegroundColor Green
}

if ($errorCount -gt 0) {
    Write-Host "  ERROR Tests    : $errorCount" -ForegroundColor Red
}
if ($skippedCount -gt 0) {
    Write-Host "  SKIPPED Tests  : $skippedCount" -ForegroundColor Yellow
}
Write-Host "========================================================" -ForegroundColor Cyan

if ($testExitCode -eq 0 -and $failedCount -eq 0 -and $errorCount -eq 0) {
    Write-Host "`n>>> [FINAL STATUS] SUCCESS: ALL $passedCount TESTS PASSED! <<<`n" -ForegroundColor Green
} else {
    Write-Host "`n>>> [FINAL STATUS] FAILURE: $failedCount TEST(S) FAILED. Review output above. <<<`n" -ForegroundColor Red
}

exit $testExitCode
