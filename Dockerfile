FROM python:3.11-slim AS backend
WORKDIR /app/backend
COPY backend/requirements.txt ./
# Force pip to use the public PyPI index to avoid inheriting a no-index/corporate mirror
RUN PIP_INDEX_URL=https://pypi.org/simple \
    python -m pip install --upgrade pip && \
    PIP_INDEX_URL=https://pypi.org/simple \
    python -m pip install --no-cache-dir -r requirements.txt
COPY backend /app/backend

FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install --production
COPY frontend /app/frontend
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

# Copy installed python packages from the backend build stage
COPY --from=backend /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend /usr/local/bin /usr/local/bin

# Copy backend
COPY --from=backend /app/backend /app/backend

# Copy frontend build to static dir served by backend (optional)
COPY --from=frontend /app/frontend/dist /app/backend/resources/frontend

ENV PYTHONPATH=/app/backend
ENV PORT=8000
EXPOSE 8000

WORKDIR /app/backend

CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
