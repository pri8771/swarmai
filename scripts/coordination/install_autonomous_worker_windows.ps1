param()
$ErrorActionPreference = "Stop"

$HostAlias = "HOST-WIN-DEV"
$SessionId = "B"
$Branch = "cursor/v2-product-lane"
$TaskName = "SwarmAI-Autonomous-Worker-B"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Source = Join-Path $Root "scripts\coordination\autonomous_worker.py"
$Base = Join-Path $env:LOCALAPPDATA "SwarmAI\autonomous-worker-$HostAlias"
$Runner = Join-Path $Base "autonomous_worker.py"
$RunnerPs = Join-Path $Base "run-autonomous-worker.ps1"
$Log = Join-Path $Base "scheduler.log"

$Gh = (Get-Command gh -ErrorAction Stop).Source
$AgentCmd = Get-Command agent -ErrorAction SilentlyContinue
if ($null -eq $AgentCmd) { $AgentCmd = Get-Command cursor-agent -ErrorAction SilentlyContinue }
if ($null -eq $AgentCmd) { throw "Cursor CLI agent is required. Install Cursor CLI, then run: agent login" }
$Agent = $AgentCmd.Source
$UvCmd = Get-Command uv -ErrorAction SilentlyContinue
if ($null -ne $UvCmd) {
    $PythonPath = (& $UvCmd.Source python find 3.12).Trim()
} else {
    $PythonPath = (Get-Command python -ErrorAction Stop).Source
}
if (-not (Test-Path $PythonPath)) { throw "Python executable not found: $PythonPath" }

New-Item -ItemType Directory -Force -Path $Base | Out-Null
Copy-Item -Force $Source $Runner

$runnerLines = @(
    '$ErrorActionPreference = "Stop"',
    '$env:SWARM_GH_PATH = ' + "'" + $Gh.Replace("'","''") + "'",
    '$env:SWARM_AGENT_PATH = ' + "'" + $Agent.Replace("'","''") + "'",
    '$log = ' + "'" + $Log.Replace("'","''") + "'",
    'try {',
    '  & ' + "'" + $PythonPath.Replace("'","''") + "'" + ' ' +
        "'" + $Runner.Replace("'","''") + "'" +
        ' --workspace ' + "'" + $Root.Replace("'","''") + "'" +
        ' --host HOST-WIN-DEV --session B --branch cursor/v2-product-lane *>> $log',
    '} catch {',
    '  ("ERROR " + (Get-Date).ToString("o") + " " + $_.Exception.Message) | Add-Content -Path $log',
    '  exit 1',
    '}'
)
Set-Content -Path $RunnerPs -Value $runnerLines -Encoding UTF8

$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument (
    '-NoProfile -ExecutionPolicy Bypass -File "' + $RunnerPs + '"'
)
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1) -RepetitionDuration (New-TimeSpan -Days 3650)
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Force | Out-Null

$env:SWARM_GH_PATH = $Gh
$env:SWARM_AGENT_PATH = $Agent
& $PythonPath $Runner --workspace $Root --host $HostAlias --session $SessionId --branch $Branch

$Info = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Host "Installed SwarmAI autonomous worker B."
Write-Host ("Workspace: " + $Root)
Write-Host ("Cursor agent: " + $Agent)
Write-Host ("Next run: " + $Info.NextRunTime)
Write-Host ("Scheduler log: " + $Log)
Write-Host "Assignment poll: every 1 minute"
