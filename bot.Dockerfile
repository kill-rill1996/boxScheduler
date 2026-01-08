FROM python:3.10-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /uvx /bin/

# Копирование файлов для uv (чтобы каждый раз не обновлять слой при изменении кода)
COPY pyproject.toml uv.lock .python-version alembic.ini /app/
RUN uv sync --locked

# Копирование файлов бота
COPY main.py /app
COPY /src /app/src
COPY /database /app/database
COPY /logs /app/logs
COPY settings.py logger.py /app/

