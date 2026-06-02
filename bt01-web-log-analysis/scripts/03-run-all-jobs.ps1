param(
    [int]$Reducers = 1
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path $PSScriptRoot -Parent
Push-Location $Root
try {
    docker exec bt01-namenode bash -lc "hdfs dfsadmin -safemode leave >/dev/null 2>&1 || true"
    docker exec bt01-namenode bash -lc "hdfs dfs -rm -r -f /bt01/output && hdfs dfs -mkdir -p /bt01/output"

    docker exec bt01-namenode bash /opt/bt01/scripts/hadoop-streaming.sh `
        bt01-normalize /logs /bt01/output/normalized normalize_mapper.py NONE 0

    docker exec bt01-namenode bash /opt/bt01/scripts/hadoop-streaming.sh `
        bt01-top-20-ips /bt01/output/normalized /bt01/output/top_ips_global top_ips_global_mapper.py top_ips_global_reducer.py 1 1

    docker exec bt01-namenode bash /opt/bt01/scripts/hadoop-streaming.sh `
        bt01-ip-counts-by-day /bt01/output/normalized /bt01/output/top_ips top_ips_mapper.py top_ips_reducer.py 1 2

    docker exec bt01-namenode bash /opt/bt01/scripts/hadoop-streaming.sh `
        bt01-status-by-day /bt01/output/normalized /bt01/output/status_by_day status_by_day_mapper.py status_by_day_reducer.py $Reducers 2

    docker exec bt01-namenode bash /opt/bt01/scripts/hadoop-streaming.sh `
        bt01-top-10-urls-by-day /bt01/output/normalized /bt01/output/top_urls_by_day top_urls_by_day_mapper.py top_urls_by_day_reducer.py 1 2

    docker exec bt01-namenode bash /opt/bt01/scripts/hadoop-streaming.sh `
        bt01-traffic-by-hour /bt01/output/normalized /bt01/output/traffic_by_hour traffic_by_hour_mapper.py traffic_by_hour_reducer.py $Reducers 2

    docker exec bt01-namenode hdfs dfs -ls -R /bt01/output
}
finally {
    Pop-Location
}
