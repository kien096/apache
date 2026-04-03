$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Push-Location $PSScriptRoot
try {
    docker compose up -d
    docker exec master hdfs dfsadmin -safemode leave | Out-Null
    docker cp .\notebooks\sample.txt master:/tmp/sample.txt
    docker exec master hdfs dfs -mkdir -p /input | Out-Null
    docker exec master hdfs dfs -put -f /tmp/sample.txt /input/sample.txt | Out-Null
    docker exec pyspark-notebook /opt/spark/bin/spark-submit --master spark://master:7077 /opt/workspace/notebooks/word_count.py
}
finally {
    Pop-Location
}
