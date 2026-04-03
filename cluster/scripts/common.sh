#!/usr/bin/env bash

set -euo pipefail

export HADOOP_HOME=/opt/hadoop
export HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
export SPARK_HOME=/opt/spark
export SPARK_CONF_DIR=/opt/spark/conf
export JAVA_HOME
JAVA_HOME="$(dirname "$(dirname "$(readlink -f "$(command -v java)")")")"
export SPARK_DIST_CLASSPATH="$($HADOOP_HOME/bin/hadoop classpath)"
export PATH="$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$SPARK_HOME/bin:$SPARK_HOME/sbin:$PATH"

mkdir -p /opt/spark/logs /data/hadoop/tmp /data/spark/work

wait_for_tcp() {
  local host="$1"
  local port="$2"
  local retries="${3:-60}"

  for _ in $(seq 1 "$retries"); do
    if bash -c ">/dev/tcp/${host}/${port}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done

  echo "Timed out waiting for ${host}:${port}" >&2
  return 1
}

tail_cluster_logs() {
  touch /opt/spark/logs/spark.log /var/log/hadoop/hadoop.log
  tail -F /opt/spark/logs/* /var/log/hadoop/* &
  wait $!
}
