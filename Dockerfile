FROM apache/spark:3.5.8 AS spark

FROM apache/hadoop:3.3.6

USER root

COPY --from=spark /opt/spark /opt/spark

ENV CONDA_DIR=/opt/conda
ENV PATH=/opt/conda/bin:$PATH

RUN curl -fsSL -o /tmp/miniforge.sh https://github.com/conda-forge/miniforge/releases/download/24.11.3-0/Miniforge3-Linux-x86_64.sh \
    && bash /tmp/miniforge.sh -b -p "$CONDA_DIR" \
    && rm -f /tmp/miniforge.sh \
    && "$CONDA_DIR"/bin/python --version \
    && mkdir -p /opt/spark/conf /opt/spark/logs /data/hdfs/namenode /data/hdfs/datanode /data/hdfs/secondary /data/spark/work /data/spark/recovery /opt/workspace/notebooks \
    && ln -s /opt/spark /usr/local/spark \
    && chown -R hadoop:users /opt/spark /data "$CONDA_DIR"

COPY cluster/conf/hadoop/core-site.xml /opt/hadoop/etc/hadoop/core-site.xml
COPY cluster/conf/hadoop/hdfs-site.xml /opt/hadoop/etc/hadoop/hdfs-site.xml
COPY cluster/conf/spark/spark-env.sh /opt/spark/conf/spark-env.sh
COPY cluster/conf/spark/spark-defaults.conf /opt/spark/conf/spark-defaults.conf
COPY cluster/conf/spark/workers /opt/spark/conf/workers
COPY cluster/conf/spark/log4j2.properties /opt/spark/conf/log4j2.properties
COPY cluster/scripts/common.sh /usr/local/bin/common.sh
COPY cluster/scripts/start-master-node.sh /usr/local/bin/start-master-node.sh
COPY cluster/scripts/start-worker-node.sh /usr/local/bin/start-worker-node.sh
COPY verify_spark.py /opt/workspace/verify_spark.py

RUN chmod +x /usr/local/bin/common.sh /usr/local/bin/start-master-node.sh /usr/local/bin/start-worker-node.sh \
    && chown -R hadoop:users /opt/hadoop/etc/hadoop /usr/local/bin /opt/workspace

USER hadoop

WORKDIR /opt/workspace
