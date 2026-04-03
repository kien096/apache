$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Push-Location $PSScriptRoot
try {
    docker compose up -d
    docker exec master hdfs dfsadmin -safemode leave | Out-Null
    docker cp .\notebooks\server.log master:/tmp/server.log
    docker exec master hdfs dfs -mkdir -p /input | Out-Null
    docker exec master hdfs dfs -put -f /tmp/server.log /input/server.log | Out-Null
    docker exec pyspark-notebook /opt/spark/bin/spark-submit --master spark://master:7077 /opt/workspace/notebooks/log_analysis.py
}
finally {
    Pop-Location
}
