FROM python:3.10-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /uvx /bin/

# Копирование файлов для uv (чтобы каждый раз не обновлять слой при изменении кода)
COPY pyproject.toml uv.lock .python-version /app/
RUN uv sync --locked

# Копирование файлов бота
COPY /src /app
COPY /database /app/database
COPY /logs /app/logs
COPY settings.py logger.py /app/

