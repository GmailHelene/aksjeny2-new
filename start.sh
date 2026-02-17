#!/usr/bin/env bash
set -euo pipefail

# Determine port (Railway/Render/Heroku set $PORT)
PORT="${PORT:-8080}"

echo "Starting gunicorn on 0.0.0.0:${PORT}"
exec gunicorn \
  -w "${GUNICORN_WORKERS:-2}" \
  --threads "${GUNICORN_THREADS:-4}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  -b "0.0.0.0:${PORT}" \
  wsgi:app
