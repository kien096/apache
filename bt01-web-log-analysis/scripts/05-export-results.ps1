$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path $PSScriptRoot -Parent
$ExportDir = Join-Path $Root "dashboard\export"

Push-Location $Root
try {
    New-Item -ItemType Directory -Force -Path $ExportDir | Out-Null
    Remove-Item -Force -ErrorAction SilentlyContinue "$ExportDir\*.tsv"

    $Exports = @{
        "top_ips_global.tsv" = "/bt01/output/top_ips_global/part-*";
        "top_ips.tsv" = "/bt01/output/top_ips/part-*";
        "status_by_day.tsv" = "/bt01/output/status_by_day/part-*";
        "top_urls_by_day.tsv" = "/bt01/output/top_urls_by_day/part-*";
        "traffic_by_hour.tsv" = "/bt01/output/traffic_by_hour/part-*";
    }

    foreach ($Name in $Exports.Keys) {
        $HdfsPath = $Exports[$Name]
        $Content = docker exec bt01-namenode bash -lc "hdfs dfs -cat '$HdfsPath'"
        [System.IO.File]::WriteAllLines((Join-Path $ExportDir $Name), $Content, [System.Text.UTF8Encoding]::new($false))
    }
}
finally {
    Pop-Location
}
