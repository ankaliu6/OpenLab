param(
  [Parameter(Mandatory = $true)]
  [string]$TaskId,
  [switch]$DropInput
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$taskRoot = Join-Path $projectRoot "lab-data\tasks\$TaskId"

if (-not (Test-Path $taskRoot)) {
  throw "Task not found: $taskRoot"
}

$workspacePath = Join-Path $taskRoot "workspace"
$logsPath = Join-Path $taskRoot "logs"
$inputPath = Join-Path $taskRoot "input"
$cleanupRecord = Join-Path $taskRoot "artifacts\cleanup.json"

if (Test-Path $workspacePath) {
  Remove-Item -LiteralPath $workspacePath -Recurse -Force
}

if (Test-Path $logsPath) {
  Remove-Item -LiteralPath $logsPath -Recurse -Force
}

if ($DropInput -and (Test-Path $inputPath)) {
  Remove-Item -LiteralPath $inputPath -Recurse -Force
}

$record = @{
  task_id = $TaskId
  cleaned_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
  removed = @("workspace", "logs")
  drop_input = [bool]$DropInput
}

$json = $record | ConvertTo-Json -Depth 4
[System.IO.File]::WriteAllText($cleanupRecord, $json, [System.Text.UTF8Encoding]::new($false))
Write-Host "Cleanup complete for task $TaskId"
