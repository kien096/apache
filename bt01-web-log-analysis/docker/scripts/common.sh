#!/usr/bin/env bash
set -euo pipefail

export HADOOP_HOME=/opt/hadoop
export HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
export HADOOP_COMMON_HOME=/opt/hadoop
export HADOOP_HDFS_HOME=/opt/hadoop
export HADOOP_YARN_HOME=/opt/hadoop
export HADOOP_MAPRED_HOME=/opt/hadoop
export JAVA_HOME
JAVA_HOME="$(dirname "$(dirname "$(readlink -f "$(command -v java)")")")"
export PATH="$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH"

mkdir -p /data/hadoop/tmp /var/log/hadoop

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

tail_hadoop_logs() {
  touch /var/log/hadoop/bt01.log
  tail -F /opt/hadoop/logs/* /var/log/hadoop/* 2>/dev/null &
  wait $!
}
