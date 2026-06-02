param(
    [int]$Lines = 2000000,
    [int]$Days = 3,
    [string]$StartDate = "2026-06-01"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path $PSScriptRoot -Parent
Push-Location $Root
try {
    python .\data\generate_apache_logs.py --lines $Lines --days $Days --start-date $StartDate --out .\data\raw
}
finally {
    Pop-Location
}
