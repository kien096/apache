$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path $PSScriptRoot -Parent
$BenchmarkDir = Join-Path $Root "docs"
$ResultFile = Join-Path $BenchmarkDir "benchmark-results.csv"

Push-Location $Root
try {
    "job,reducers,seconds" | Set-Content -Path $ResultFile -Encoding UTF8

    foreach ($Reducers in @(1, 2, 4)) {
        foreach ($Job in @("status_by_day", "traffic_by_hour")) {
            $Start = Get-Date
            if ($Job -eq "status_by_day") {
                docker exec bt01-namenode bash /opt/bt01/scripts/hadoop-streaming.sh `
                    "benchmark-status-$Reducers" /bt01/output/normalized "/bt01/benchmark/status_by_day_r$Reducers" status_by_day_mapper.py status_by_day_reducer.py $Reducers 2
            }
            else {
                docker exec bt01-namenode bash /opt/bt01/scripts/hadoop-streaming.sh `
                    "benchmark-hour-$Reducers" /bt01/output/normalized "/bt01/benchmark/traffic_by_hour_r$Reducers" traffic_by_hour_mapper.py traffic_by_hour_reducer.py $Reducers 2
            }
            $Seconds = [Math]::Round(((Get-Date) - $Start).TotalSeconds, 2)
            "$Job,$Reducers,$Seconds" | Add-Content -Path $ResultFile -Encoding UTF8
        }
    }

    Get-Content $ResultFile
}
finally {
    Pop-Location
}
