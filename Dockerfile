FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY bot ./bot

# Создание директорий для данных и логов
RUN mkdir -p /app/data /app/logs

# Запуск
CMD ["uvicorn", "bot.main:app", "--host", "0.0.0.0", "--port", "9010"]