$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Push-Location $PSScriptRoot
try {
    docker compose up -d

    Write-Host ""
    Write-Host "Lab is running:"
    Write-Host "Spark UI   : http://localhost:8080"
    Write-Host "HDFS UI    : http://localhost:9870"
    Write-Host "Jupyter    : http://localhost:8888"
}
finally {
    Pop-Location
}
