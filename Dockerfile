# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libffi-dev \
       libssl-dev \
       libjpeg-dev \
       zlib1g-dev \
       libfreetype6-dev \
       libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and build wheels
COPY backend/requirements.txt /tmp/requirements.txt
# Limit parallel builds to prevent OOM on low-memory systems (Ubuntu 20)
# MAX_JOBS=1 forces sequential compilation to reduce memory usage
RUN pip install --upgrade pip \
    && MAX_JOBS=1 pip wheel --no-cache-dir --wheel-dir /wheels \
       --default-timeout=10000 --retries 5 \
       -r /tmp/requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Install only runtime libraries (no build tools)
# Note: python:3.12-slim is based on Debian 12 (Bookworm)
# For compatibility with host Ubuntu 20, use Debian 12 package names
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libffi8t64 \
       libssl3t64 \
       libjpeg62-turbo \
       zlib1g \
       libfreetype6 \
       libpng16-16t64 \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built wheels from builder stage
COPY --from=builder /wheels /wheels

# Install from wheels (much faster, no compilation needed)
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* \
    && rm -rf /wheels

# Copy application code
COPY backend /app

ENV PYTHONPATH=/app
ENV PORT=8000
ENV HOST=0.0.0.0
EXPOSE 8000

CMD ["python", "main.py"]
