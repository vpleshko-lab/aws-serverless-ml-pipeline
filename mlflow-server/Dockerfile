FROM python:3.12-slim

# Робочу папку
WORKDIR /mlflow

# Копіюємо залежності
COPY requirements.txt .

# Встановлюємо пакети без збереження кешу
RUN pip install --no-cache-dir -r requirements.txt

# Експонуємо порт 5000 (стандартний порт для MLflow UI)
EXPOSE 5000

# Команду запуску в mlflow-server/Dockerfile
CMD mlflow server \
    --host 0.0.0.0 \
    --port 5000 \
    --backend-store-uri postgresql://${DB_USERNAME}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME} \
    --default-artifact-root s3://serverless-models-artifacts/artifacts/
