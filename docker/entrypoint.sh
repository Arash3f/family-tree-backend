#!/bin/sh
set -e

POSTGRES_HOST="${POSTGRES_HOST:-db}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

echo "Waiting for database at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
python -c "
import os
import socket
import time

host = os.environ.get('POSTGRES_HOST', 'db')
port = int(os.environ.get('POSTGRES_PORT', '5432'))

while True:
    try:
        with socket.create_connection((host, port), timeout=1):
            break
    except OSError:
        time.sleep(1)
"
echo "Database is UP!"

echo "Running migrations..."
alembic upgrade head

echo "Starting app..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8001
