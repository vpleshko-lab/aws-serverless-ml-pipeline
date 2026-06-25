FROM python:3.12-slim

ARG CACHEBUST=1

# Робочу папку
ENV PYTHONUNBUFFERED=1
WORKDIR /mlflow

# Гарантовано оновлюємо pip та ставимо setuptools у систему
RUN pip install --no-cache-dir pip==24.0 setuptools==70.3.0

# Копіюємо залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Експонуємо порт 5000 (стандартний порт для MLflow UI)
EXPOSE 5000

# Команду запуску в mlflow-server/Dockerfile
CMD ["sh", "-c", "mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri postgresql://${DB_USERNAME}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME} --default-artifact-root s3://serverless-models-artifacts/artifacts/"]
