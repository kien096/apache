#!/usr/bin/env bash
set -euo pipefail

source /opt/bt01/docker-scripts/common.sh

cleanup() {
  mapred --daemon stop historyserver >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

wait_for_tcp namenode 9000 90
mapred --daemon start historyserver

tail_hadoop_logs
