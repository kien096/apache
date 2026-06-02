$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    docker compose up -d

    Write-Host "Waiting for HDFS and YARN..."
    docker exec bt01-namenode bash -lc "for i in {1..60}; do hdfs dfs -ls / >/dev/null 2>&1 && exit 0; sleep 2; done; exit 1"
    docker exec bt01-resourcemanager bash -lc "for i in {1..60}; do yarn node -list >/dev/null 2>&1 && exit 0; sleep 2; done; exit 1"

    Write-Host ""
    Write-Host "BT01 cluster is running:"
    Write-Host "HDFS UI           : http://localhost:9871"
    Write-Host "YARN UI           : http://localhost:8089"
    Write-Host "MapReduce History : http://localhost:19889"
    Write-Host "Grafana           : http://localhost:3001  admin/admin"
    Write-Host "PostgreSQL        : localhost:5433  bt01/bt01"
}
finally {
    Pop-Location
}
