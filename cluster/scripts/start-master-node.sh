#!/usr/bin/env bash

set -euo pipefail

source /usr/local/bin/common.sh

cleanup() {
  "$SPARK_HOME"/sbin/stop-master.sh >/dev/null 2>&1 || true
  "$HADOOP_HOME"/bin/hdfs --daemon stop secondarynamenode >/dev/null 2>&1 || true
  "$HADOOP_HOME"/bin/hdfs --daemon stop namenode >/dev/null 2>&1 || true
}

trap cleanup EXIT INT TERM

if [ ! -f /data/hdfs/namenode/current/VERSION ]; then
  "$HADOOP_HOME"/bin/hdfs namenode -format -force -nonInteractive
fi

"$HADOOP_HOME"/bin/hdfs --daemon start namenode
"$HADOOP_HOME"/bin/hdfs --daemon start secondarynamenode

wait_for_tcp master 9000 90

"$HADOOP_HOME"/bin/hdfs dfs -mkdir -p /spark-logs /spark-events || true
"$HADOOP_HOME"/bin/hdfs dfs -chmod 777 /spark-logs /spark-events || true

"$SPARK_HOME"/sbin/start-master.sh

tail_cluster_logs
