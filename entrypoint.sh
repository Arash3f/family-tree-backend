#!/bin/sh
set -e

echo "Waiting for database..."
python -c "
import socket
import time
while True:
    try:
        with socket.create_connection(('db', 5432), timeout=1):
            break
    except OSError:
        time.sleep(1)
"
echo "Database is UP!"

echo "Running migrations..."
alembic upgrade head

echo "Starting app..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8001
