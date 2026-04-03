#!/usr/bin/env bash

set -euo pipefail

source /usr/local/bin/common.sh

cleanup() {
  "$SPARK_HOME"/sbin/stop-worker.sh >/dev/null 2>&1 || true
  "$HADOOP_HOME"/bin/hdfs --daemon stop datanode >/dev/null 2>&1 || true
}

trap cleanup EXIT INT TERM

wait_for_tcp master 9000 90
wait_for_tcp master 7077 90

"$HADOOP_HOME"/bin/hdfs --daemon start datanode
"$SPARK_HOME"/sbin/start-worker.sh spark://master:7077

tail_cluster_logs
