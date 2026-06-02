#!/usr/bin/env bash
set -euo pipefail

source /opt/bt01/docker-scripts/common.sh

cleanup() {
  hdfs --daemon stop namenode >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

mkdir -p /data/hdfs/namenode
if [ ! -f /data/hdfs/namenode/current/VERSION ]; then
  hdfs namenode -format -force -nonInteractive
fi

hdfs --daemon start namenode
wait_for_tcp namenode 9000 90
hdfs dfs -mkdir -p /logs /bt01/output /tmp/hadoop-yarn/staging/history/done_intermediate || true
hdfs dfs -chmod -R 777 /logs /bt01 /tmp || true

tail_hadoop_logs
