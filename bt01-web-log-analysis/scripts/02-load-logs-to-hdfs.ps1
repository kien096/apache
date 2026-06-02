$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path $PSScriptRoot -Parent
$Raw = Join-Path $Root "data\raw"
if (-not (Test-Path $Raw)) {
    throw "Missing data\raw. Run scripts\01-generate-logs.ps1 first."
}

Push-Location $Root
try {
    docker exec bt01-namenode bash -lc "rm -rf /tmp/bt01-raw && mkdir -p /tmp/bt01-raw"
    docker cp ".\data\raw\." "bt01-namenode:/tmp/bt01-raw/"
    docker exec bt01-namenode bash /opt/bt01/scripts/load-logs-to-hdfs.sh
}
finally {
    Pop-Location
}
