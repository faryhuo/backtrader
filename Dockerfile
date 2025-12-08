FROM python:3.11-slim AS backend
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app/backend
COPY backend/requirements.txt ./requirements.txt
# Longer timeout/retries help in slow networks; no cache keeps the layer small
RUN pip3 install --no-cache-dir --default-timeout=10000 --retries 5 -r requirements.txt
COPY backend /app/backend

ENV PYTHONPATH=/app/backend
ENV PORT=8000
EXPOSE 8000

WORKDIR /app/backend

CMD ["python", "main.py"]
