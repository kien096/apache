#!/usr/bin/env bash

set -euo pipefail

for _ in $(seq 1 90); do
  if bash -c ">/dev/tcp/master/7077" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

mkdir -p /opt/workspace/notebooks
mkdir -p /root/.local/share/jupyter/runtime
cd /opt/workspace/notebooks

export HOME=/root
export JUPYTER_RUNTIME_DIR=/root/.local/share/jupyter/runtime
export PYSPARK_PYTHON=/opt/conda/bin/python
export PYTHONPATH="/opt/spark/python/lib/pyspark.zip:/opt/spark/python/lib/py4j-0.10.9.7-src.zip:${PYTHONPATH:-}"

exec /opt/conda/bin/jupyter-notebook \
  --ip=0.0.0.0 \
  --port=8888 \
  --no-browser \
  --allow-root \
  --NotebookApp.token= \
  --NotebookApp.password=
