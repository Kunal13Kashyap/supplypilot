#!/bin/sh
set -e
echo "Waiting for PostgreSQL..."
python - <<'PY'
import os, time
import socket

host = os.environ.get("POSTGRES_HOST", "postgres")
port = int(os.environ.get("POSTGRES_PORT", "5432"))
for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit("PostgreSQL not reachable")
PY

echo "Running migrations..."
alembic upgrade head

echo "Seeding demo data..."
python -m scripts.seed

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
