#!/usr/bin/env bash
set -euo pipefail

source /opt/bt01/docker-scripts/common.sh

cleanup() {
  hdfs --daemon stop datanode >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

mkdir -p /data/hdfs/datanode
wait_for_tcp namenode 9000 90
hdfs --daemon start datanode

tail_hadoop_logs
