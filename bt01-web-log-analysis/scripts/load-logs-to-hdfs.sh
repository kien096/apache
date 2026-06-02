#!/usr/bin/env bash
set -euo pipefail

hdfs dfsadmin -safemode leave >/dev/null 2>&1 || true
hdfs dfs -mkdir -p /logs

find /tmp/bt01-raw -type f -name "*.log" | sort | while read -r file; do
  rel="${file#/tmp/bt01-raw/}"
  dir="$(dirname "$rel")"
  hdfs dfs -mkdir -p "/logs/$dir"
  hdfs dfs -put -f "$file" "/logs/$dir/"
  echo "Loaded $file -> /logs/$dir/"
done

hdfs dfs -ls -R /logs
