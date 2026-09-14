# syntax=docker/dockerfile:1
FROM debian:bookworm-slim AS base
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    PL_DATA_DIR=/data PL_WEB_PORT=8077 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
    OPENCV_FFMPEG_CAPTURE_OPTIONS="rtsp_transport;tcp|fflags;nobuffer|flags;low_delay"
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates python3 python3-venv python3-opencv \
    && rm -rf /var/lib/apt/lists/*

FROM base AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3-dev libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY pyproject.toml docker-constraints.txt ./
COPY src ./src
RUN python3 -m venv --system-site-packages /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --constraint docker-constraints.txt . \
    && /opt/venv/bin/python -c "import cv2; import wingxtra_pl.main; assert hasattr(cv2, 'aruco')"

FROM base AS runtime
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app
ARG VCS_REF=unknown
LABEL org.opencontainers.image.title="Wingxtra Precision Landing" \
      org.opencontainers.image.description="Calibrated multi-tag landing target service for BlueOS" \
      org.opencontainers.image.source="https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.version="1.0.0-rc.2" \
      org.opencontainers.image.revision=$VCS_REF
LABEL version="1.0.0-rc.2" \
      type="device-integration" \
      tags='["navigation","positioning","camera"]' \
      authors='[{"name":"Wingxtra Aerospace Ltd."}]' \
      company='{"name":"Wingxtra Aerospace Ltd.","about":"Multi-tag precision landing"}' \
      readme="https://raw.githubusercontent.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/main/README.md" \
      links='{"github":"https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing"}' \
      permissions='{"ExposedPorts":{"8077/tcp":{}},"HostConfig":{"NetworkMode":"host","Binds":["/usr/blueos/extensions/wingxtra-precision-landing:/data"],"RestartPolicy":{"Name":"unless-stopped"},"CapDrop":["ALL"],"SecurityOpt":["no-new-privileges:true"],"CpuPeriod":100000,"CpuQuota":200000,"Memory":1073741824,"PidsLimit":256}}'
EXPOSE 8077
HEALTHCHECK --interval=15s --timeout=3s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8077/health', timeout=2)" || exit 1
CMD ["wingxtra-pl", "--data-dir", "/data", "--host", "0.0.0.0", "--port", "8077"]

FROM runtime AS test
COPY tests /tests
COPY landing-target.json /landing-target.json
RUN pip install --no-cache-dir pytest==9.0.2 httpx==0.28.1
WORKDIR /
RUN python -m pytest -q /tests

# The default target is the runtime image, never the test layer.
FROM runtime AS final
