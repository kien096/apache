$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path $PSScriptRoot -Parent
$ExportDir = Join-Path $Root "dashboard\export"
if (-not (Test-Path $ExportDir)) {
    throw "Missing dashboard\export. Run scripts\05-export-results.ps1 first."
}

Push-Location $Root
try {
    Get-Content ".\dashboard\postgres\init.sql" | docker exec -i bt01-postgres psql -U bt01 -d bt01_logs

    docker cp ".\dashboard\export\top_ips.tsv" "bt01-postgres:/tmp/top_ips.tsv"
    docker cp ".\dashboard\export\status_by_day.tsv" "bt01-postgres:/tmp/status_by_day.tsv"
    docker cp ".\dashboard\export\top_urls_by_day.tsv" "bt01-postgres:/tmp/top_urls_by_day.tsv"
    docker cp ".\dashboard\export\traffic_by_hour.tsv" "bt01-postgres:/tmp/traffic_by_hour.tsv"

    $Sql = @'
TRUNCATE top_ips, status_by_day, top_urls_by_day, traffic_by_hour;
\copy top_ips(day, ip, hits) FROM '/tmp/top_ips.tsv' WITH (FORMAT text, DELIMITER E'\t');
\copy status_by_day(day, status, hits) FROM '/tmp/status_by_day.tsv' WITH (FORMAT text, DELIMITER E'\t');
\copy top_urls_by_day(day, url, hits) FROM '/tmp/top_urls_by_day.tsv' WITH (FORMAT text, DELIMITER E'\t');
\copy traffic_by_hour(day, hour, hits) FROM '/tmp/traffic_by_hour.tsv' WITH (FORMAT text, DELIMITER E'\t');
'@
    $Sql | docker exec -i bt01-postgres psql -U bt01 -d bt01_logs
}
finally {
    Pop-Location
}
