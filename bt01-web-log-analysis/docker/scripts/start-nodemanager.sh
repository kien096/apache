#!/usr/bin/env bash
set -euo pipefail

source /opt/bt01/docker-scripts/common.sh

cleanup() {
  yarn --daemon stop nodemanager >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

mkdir -p /data/yarn/local /data/yarn/logs
wait_for_tcp resourcemanager 8032 90
wait_for_tcp namenode 9000 90
yarn --daemon start nodemanager

tail_hadoop_logs
