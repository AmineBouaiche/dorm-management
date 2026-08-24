#!/bin/sh
set -eu

alembic upgrade head
python scripts/seed_demo_data.py
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --no-server-header
