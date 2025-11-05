FROM python:3.13-slim

WORKDIR /app

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка зависимостей
COPY pyproject.toml poetry.lock* /app/
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --without dev --no-root --no-interaction --no-ansi

# Копирование проекта
COPY . .

# Создание статических файлов
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
