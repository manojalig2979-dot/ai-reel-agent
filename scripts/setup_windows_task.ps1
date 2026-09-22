# PowerShell Script to Register Daily Scheduled Task in Windows
$TaskName = "AIReelDailyPublisher"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VbsPath = Join-Path $ScriptDir "run_daily_background.vbs"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "    AI Reel Generator - Windows Scheduled Task Setup   " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Check if task already exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "[INFO] Task '$TaskName' already exists. Updating schedule to 09:00 PM..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$Action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$VbsPath`""
$Trigger = New-ScheduledTaskTrigger -Daily -At "09:00PM"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Automated Daily AI Reel Generator and Publisher (9:00 PM)"

Write-Host ""
Write-Host "[SUCCESS] Windows Daily Scheduled Task registered successfully!" -ForegroundColor Green
Write-Host "Task Name : $TaskName" -ForegroundColor White
Write-Host "Schedule  : Runs every day at 09:00 PM in the background" -ForegroundColor White
Write-Host "Launcher  : $VbsPath" -ForegroundColor White
Write-Host ""
