FROM python:3.10-slim

WORKDIR /app

# Копирование файлов для uv (чтобы каждый раз не обновлять слой при изменении кода)
COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /uvx /bin/
COPY pyproject.toml uv.lock .python-version /app/
RUN uv sync --locked

COPY /app /app/app
COPY /database /app/database
COPY /logs /app/logs
COPY settings.py logger.py /app/

CMD ["uv", "run", "fastapi", "run", "app/main.py", "--port", "8000"]