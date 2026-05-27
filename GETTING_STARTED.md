# Як застосувати зміни у локальний репо

## 🚀 Один рядок для старту

```bash
git fetch origin && git checkout agents/infrastructure-template-setup && poetry install
```

Потім в двох терміналах:

```bash
# Terminal 1
poetry run uvicorn app.app_main:app --reload

# Terminal 2
poetry run streamlit run app/streamlit_ui.py
```

Відкрити: **http://localhost:8501**

---

## 📋 Детальні кроки

### Крок 1: Синхронізація з сервером

```bash
cd /path/to/your/repo

# Завантажити всі гілки з GitHub
git fetch origin

# Перейти на гілку з новими змінами
git checkout agents/infrastructure-template-setup
```

**Альтернатива** (якщо змін в main):
```bash
git checkout main
git pull origin main
```

### Крок 2: Встановити залежності

```bash
poetry install
```

Це додасть:
- **Streamlit 1.57.0** — Web UI фреймворк
- **Requests 2.31.0+** — HTTP клієнт для API

### Крок 3: Запустити локально

**Terminal 1 — FastAPI backend:**
```bash
poetry run uvicorn app.app_main:app --reload
```

Вихід:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Terminal 2 — Streamlit UI:**
```bash
poetry run streamlit run app/streamlit_ui.py
```

Браузер автоматично відкриється на:
```
http://localhost:8501
```

### Крок 4: Тестування

1. Відкрити Streamlit UI: http://localhost:8501
2. Завантажити зображення (є тестове у `tests/data/dog_001.avif`)
3. Натиснути "Run Inference"
4. Побачити результат з впевненістю та latency

---

## 🎯 Швидкі команди

### Перевірити статус
```bash
git status
git log --oneline -1
```

### Перевірити нові файли
```bash
ls infrastructure/
cat app/streamlit_ui.py | head -20
```

### Перевірити залежності
```bash
poetry show | grep -E "streamlit|requests"
```

---

## 🛠️ Інтерактивний старт

```bash
chmod +x quickstart.sh
./quickstart.sh
```

Вибрати:
- `1` для локального тестування (FastAPI + Streamlit)
- `2` для розгортання на AWS (потребує SAM CLI)

---

## 📁 Що отримаєте локально

```
aws-serverless-ml-pipeline/
├── infrastructure/
│   ├── template.yaml        ← AWS SAM (CloudFormation)
│   ├── mlflow_lambda.py     ← MLFlow tracking Lambda
│   ├── deploy.sh            ← Автоматизація розгортання
│   ├── parameters.json      ← Параметри
│   └── README.md            ← IaC документація
├── app/
│   ├── streamlit_ui.py      ← NEW Web UI
│   ├── app_main.py          ← FastAPI (unchanged)
│   └── ...
├── quickstart.sh            ← Interactive setup
├── README.md                ← UPDATED Документація
├── pyproject.toml           ← UPDATED Залежності
└── ...
```

---

## ❓ Поширені питання

### Де мій репозиторій?
```bash
git rev-parse --show-toplevel
```

### Як дізнатися поточну гілку?
```bash
git branch --show-current
```

### Як переглянути дерево змін?
```bash
git log --oneline --graph --all | head -20
```

### Як повернутися на main?
```bash
git checkout main
```

### Конфлікти при синхронізації?
```bash
# Скасувати поточну операцію
git merge --abort
# або
git rebase --abort
```

### Сніжити порт 8000 або 8501?
```bash
# FastAPI на іншому порту
poetry run uvicorn app.app_main:app --port 8001 --reload

# Streamlit на іншому порту
poetry run streamlit run app/streamlit_ui.py --server.port 8502
```

---

## 🚀 AWS розгортання (опціонально)

Потребує: **AWS CLI** + **SAM CLI**

```bash
# Встановити SAM CLI (macOS)
brew install aws-sam-cli

# Встановити AWS CLI
brew install awscli
# або
pip install awscli

# Налаштувати AWS credentials
aws configure

# Розгорнути
cd infrastructure
chmod +x deploy.sh
./deploy.sh ml-inference-pipeline-dev us-east-1 dev
```

---

## 📚 Документація

- **README.md** — Загальна документація, архітектура, production checklist
- **infrastructure/README.md** — IaC гайд, розгортання, troubleshooting
- **app/streamlit_ui.py** — Код веб-інтерфейсу (документований)
- **infrastructure/template.yaml** — AWS SAM шаблон (детальні коментарі)

---

## ✅ Все готово!

Зміни вже локальні. Просто виконайте команди вище і почніть розробку.

**Приємної роботи!** 🎉
