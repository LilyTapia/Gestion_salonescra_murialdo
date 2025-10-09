#!/usr/bin/env bash
set -e

# Wait for MySQL
echo "Waiting for MySQL at $DB_HOST:$DB_PORT ..."
until python - <<'PY'
import os, sys, time
import socket
h = os.environ.get("DB_HOST", "db")
p = int(os.environ.get("DB_PORT", "3306"))
s = socket.socket()
s.settimeout(1.0)
try:
    s.connect((h, p))
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
do
  echo "DB not ready, retrying..."
  sleep 2
done

echo "Applying migrations..."
python manage.py migrate

echo "Seeding base data..."
python manage.py create_sample_users || true
python manage.py seed_data || true

echo "Starting Django dev server on 0.0.0.0:8000"
exec python manage.py runserver 0.0.0.0:8000
