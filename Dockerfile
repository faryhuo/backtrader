FROM python:3.11-slim AS backend
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip3 install -r requirements.txt
COPY backend /app/backend

FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install --production
COPY frontend /app/frontend
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

# Copy backend
COPY --from=backend /app/backend /app/backend

# Copy frontend build to static dir served by backend (optional)
COPY --from=frontend /app/frontend/dist /app/backend/resources/frontend

ENV PYTHONPATH=/app/backend
ENV PORT=8000
EXPOSE 8000

WORKDIR /app/backend

CMD ["python", "main.py"]
