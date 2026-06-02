$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    docker compose down
}
finally {
    Pop-Location
}
