$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$serverPath = Join-Path $projectRoot "lab\open_lab.py"

if (-not (Test-Path $serverPath)) {
  throw "Open Lab server not found: $serverPath"
}

$hostAddress = if ($env:OPEN_LAB_HOST) { $env:OPEN_LAB_HOST } else { "127.0.0.1" }
$portValue = if ($env:OPEN_LAB_PORT) { $env:OPEN_LAB_PORT } else { "8765" }

python $serverPath serve --host $hostAddress --port $portValue
