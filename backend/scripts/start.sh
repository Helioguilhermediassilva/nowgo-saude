#!/usr/bin/env sh
# Production entrypoint: apply pending Alembic migrations, then start uvicorn.
set -eu

PORT="${PORT:-8000}"

echo "[start.sh] running alembic upgrade head..."
alembic upgrade head

echo "[start.sh] starting uvicorn on 0.0.0.0:${PORT}..."
exec uvicorn nowgo_saude.main:app --host 0.0.0.0 --port "${PORT}"
