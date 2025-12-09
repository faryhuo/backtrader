# syntax=docker/dockerfile:1.4
# Build stage: install build deps and build wheels
FROM python:3.12-slim AS builder
WORKDIR /app

# 只在 build 阶段安装编译依赖（减少最终镜像体积）
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
       build-essential \
       libffi-dev \
       libssl-dev \
       libjpeg-dev \
       zlib1g-dev \
       libfreetype6-dev \
       libpng-dev \
       ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# 复制 requirements 并构建 wheel 到 /wheels
COPY backend/requirements.txt /tmp/requirements.txt

# 使用 BuildKit 缓存 pip 下载和 wheel 构建，加快重复构建
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/pip/http \
    python -m pip install --upgrade pip setuptools wheel \
    && python -m pip wheel --wheel-dir=/wheels -r /tmp/requirements.txt

# Runtime stage: 小巧运行镜像，只安装 wheels
FROM python:3.12-slim AS runtime
WORKDIR /app

# 运行时只安装必要的系统库（不含编译工具）
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
       libjpeg62-turbo \
       libfreetype6 \
       zlib1g \
 && rm -rf /var/lib/apt/lists/*

# 拷贝 wheel 文件并从本地 wheel 安装（离线安装，避免重编译）
COPY --from=builder /wheels /wheels
RUN python -m pip install --upgrade pip \
 && python -m pip install --no-index --find-links=/wheels -r /wheels/../tmp/requirements.txt || \
    # fallback: 如果某些包在 wheel 中缺失，允许 pip 从网络拉取
    python -m pip install -r /tmp/requirements.txt

# 复制应用代码（放在最后，保证依赖变更才重新安装）
COPY backend /app

ENV PYTHONPATH=/app
ENV PORT=8000
EXPOSE 8000

CMD ["python", "main.py"]
