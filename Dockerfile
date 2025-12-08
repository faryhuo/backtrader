FROM python:3.12-slim
WORKDIR /app

COPY backend /app
RUN pip install --no-cache-dir --default-timeout=10000 --retries 5 -r requirements.txt

ENV PYTHONPATH=/app
ENV PORT=8000
EXPOSE 8000

CMD ["python", "main.py"]
