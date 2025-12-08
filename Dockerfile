FROM python:3.12-slim

WORKDIR /app

# Install system packages needed to build wheels (pandas/matplotlib can fall back to source)
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

# Copy and install Python deps first for better build caching
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --default-timeout=10000 --retries 5 -r /tmp/requirements.txt

# Copy application code
COPY backend /app

ENV PYTHONPATH=/app
ENV PORT=8000
EXPOSE 8000

CMD ["python", "main.py"]
