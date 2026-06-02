#!/usr/bin/env bash
set -euo pipefail

source /opt/bt01/docker-scripts/common.sh

cleanup() {
  yarn --daemon stop resourcemanager >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

yarn --daemon start resourcemanager
wait_for_tcp resourcemanager 8088 90

tail_hadoop_logs
