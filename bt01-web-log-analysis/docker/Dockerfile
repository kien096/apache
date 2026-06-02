FROM apache/hadoop:3.3.6

USER root

ENV CONDA_DIR=/opt/conda
ENV PATH=/opt/conda/bin:$PATH

RUN curl -fsSL -o /tmp/miniforge.sh https://github.com/conda-forge/miniforge/releases/download/24.11.3-0/Miniforge3-Linux-x86_64.sh \
    && bash /tmp/miniforge.sh -b -p "$CONDA_DIR" \
    && rm -f /tmp/miniforge.sh \
    && ln -sf "$CONDA_DIR/bin/python" /usr/local/bin/python3 \
    && python3 --version
