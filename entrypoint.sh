#!/usr/bin/env bash
set -euo pipefail

cd /app

# Load environment variables from /app/.env for child processes (optional)
if [ -f /app/.env ]; then
  set -a
  . /app/.env
  set +a
fi

# Apply migrations and collect static
#python manage.py makemigrations --noinput || true
#python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Start Redis (no persistence) in background
redis-server --save "" --appendonly no &
REDIS_PID=$!
echo "Started redis-server PID=${REDIS_PID}"

# Configure Gunicorn defaults (can be overridden via env)
: "${GUNICORN_WORKERS:=4}"
: "${GUNICORN_TIMEOUT:=120}"
: "${GUNICORN_BIND:=127.0.0.1:8000}"

# Start Gunicorn in background (ASGI with Uvicorn workers)
/usr/local/bin/gunicorn fresh_cart.asgi:application \
  --bind "${GUNICORN_BIND}" \
  --workers "${GUNICORN_WORKERS}" \
  --worker-class uvicorn.workers.UvicornWorker \
  --access-logfile - \
  --error-logfile - \
  --timeout "${GUNICORN_TIMEOUT}" &
GUNICORN_PID=$!
echo "Started gunicorn PID=${GUNICORN_PID}"

# Graceful shutdown
terminate() {
  echo "Received signal, stopping services..."
  kill -TERM "$GUNICORN_PID" 2>/dev/null || true
  kill -TERM "$REDIS_PID" 2>/dev/null || true
  sleep 5 || true
  kill -KILL "$GUNICORN_PID" 2>/dev/null || true
  kill -KILL "$REDIS_PID" 2>/dev/null || true
}
trap terminate INT TERM

# Start Nginx in foreground
exec /usr/sbin/nginx -g "daemon off;"
