param()
$ErrorActionPreference = "Stop"

$HostAlias = "HOST-WIN-DEV"
$SessionId = "B"
$Branch = "cursor/v2-product-lane"
$TaskName = "SwarmAI-Coord-Heartbeat-B"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Source = Join-Path $Root "scripts\coordination\heartbeat.py"
$Base = Join-Path $env:LOCALAPPDATA "SwarmAI\coord-heartbeat-$HostAlias"
$HeartbeatCopy = Join-Path $Base "heartbeat.py"
$RunnerPs = Join-Path $Base "run-heartbeat.ps1"
$SchedulerLog = Join-Path $Base "scheduler.log"

$Gh = (Get-Command gh -ErrorAction Stop).Source
$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $PythonCmd) {
    $Uv = (Get-Command uv -ErrorAction Stop).Source
    $PythonPath = (& $Uv python find 3.12).Trim()
} else {
    $PythonPath = $PythonCmd.Source
}
if (-not (Test-Path $PythonPath)) { throw "Python executable not found: $PythonPath" }

New-Item -ItemType Directory -Force -Path $Base | Out-Null
Copy-Item -Force $Source $HeartbeatCopy

$runnerLines = @(
    '$ErrorActionPreference = "Stop"',
    '$env:SWARM_GH_PATH = ' + "'" + $Gh.Replace("'","''") + "'",
    '$log = ' + "'" + $SchedulerLog.Replace("'","''") + "'",
    'try {',
    '  & ' + "'" + $PythonPath.Replace("'","''") + "'" + ' ' +
        "'" + $HeartbeatCopy.Replace("'","''") + "'" +
        ' --host HOST-WIN-DEV --session B --branch cursor/v2-product-lane --trigger scheduler *>> $log',
    '} catch {',
    '  ("ERROR " + (Get-Date).ToString("o") + " " + $_.Exception.Message) | Add-Content -Path $log',
    '  exit 1',
    '}'
)
Set-Content -Path $RunnerPs -Value $runnerLines -Encoding UTF8

$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument (
    '-NoProfile -ExecutionPolicy Bypass -File "' + $RunnerPs + '"'
)
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 3650)
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Force | Out-Null

$env:SWARM_GH_PATH = $Gh
& $PythonPath $HeartbeatCopy --host $HostAlias --session $SessionId --branch $Branch --trigger install --force
$Task = Get-ScheduledTask -TaskName $TaskName
$Info = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Host "Installed SwarmAI coordination heartbeat B."
Write-Host ("Task state: " + $Task.State)
Write-Host ("Next run: " + $Info.NextRunTime)
Write-Host ("Scheduler log: " + $SchedulerLog)
Write-Host "Scheduler wakes every 5m; client self-throttles to the cadence in HEARTBEAT_STATE.json."
