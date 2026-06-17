FROM python:3.12-slim

# Робочу папку
WORKDIR /mlflow

# Копіюємо залежності
COPY requirements.txt .

# Встановлюємо пакети без збереження кешу
RUN pip install --no-cache-dir -r requirements.txt

# Експонуємо порт 5000 (стандартний порт для MLflow UI)
EXPOSE 5000

# Команда запуску сервера. Значення хоста 0.0.0.0 обов'язкове, щоб ECS міг прокинути порт назовні
ENTRYPOINT ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000"]
