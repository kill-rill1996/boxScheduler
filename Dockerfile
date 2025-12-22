FROM python:3.11-slim

# Устанавливаем uv
RUN pip install uv

WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости через uv
RUN uv pip install --system -r pyproject.toml

# Копируем исходный код
COPY src/ ./src/