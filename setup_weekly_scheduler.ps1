# ====================================================================
# ShopSense - Automated Windows Task Scheduler Setup for Weekly Agent
# ====================================================================

[CmdletBinding()]
param(
    [switch]$Uninstall,
    [string]$Time = "08:00",
    [string]$DayOfWeek = "Monday"
)

$taskName = "ShopSenseWeeklyAIAgent"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptPath = Join-Path $projectRoot "run_weekly_agent.ps1"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  ShopSense - Automated Weekly Agent Task Scheduler     " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

if ($Uninstall) {
    Write-Host "`nUnregistering scheduled task '$taskName'..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "[SUCCESS] Task '$taskName' successfully removed." -ForegroundColor Green
    exit 0
}

Write-Host "`nConfiguring automated weekly execution for ShopSense AI Agent..." -ForegroundColor Yellow
Write-Host "  • Target Script : $scriptPath -All" -ForegroundColor Gray
Write-Host "  • Schedule      : Every $DayOfWeek at $Time" -ForegroundColor Gray

# Define Action
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -All" `
    -WorkingDirectory $projectRoot

# Define Weekly Trigger
$trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek $DayOfWeek `
    -At $Time

# Define Settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

# Register or update task
try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Automated weekly business analytics and email report generation for ShopSense approved vendors." `
        -Force | Out-Null

    Write-Host "`n[SUCCESS] Scheduled Task '$taskName' registered successfully!" -ForegroundColor Green
    Write-Host "The ShopSense AI Agent will run automatically every $DayOfWeek at $Time." -ForegroundColor Green
    Write-Host "`nTo check status in PowerShell: Get-ScheduledTask -TaskName '$taskName'" -ForegroundColor Cyan
    Write-Host "To remove task anytime: .\setup_weekly_scheduler.ps1 -Uninstall" -ForegroundColor Cyan
} catch {
    Write-Host "`n[NOTE] Registering a scheduled task may require Administrator privileges." -ForegroundColor Yellow
    Write-Host "Error details: $_" -ForegroundColor Red
    Write-Host "Alternatively, the In-App background scheduler inside FastAPI automatically executes weekly without Task Scheduler." -ForegroundColor Green
}
