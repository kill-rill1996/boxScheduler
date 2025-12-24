FROM python:3.10-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /uvx /bin/

COPY /src /app
COPY /database /app/database
COPY /logs /app/logs
COPY settings.py pyproject.toml uv.lock .python-version logger.py /app/

WORKDIR /app

RUN uv sync --locked # pip install -r requirements.txt

