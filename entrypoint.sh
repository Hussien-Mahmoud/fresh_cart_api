#!/usr/bin/env bash
set -e

# Wait for Postgres
#python - <<'PY'
#import os, time, sys
#import psycopg2
#host=os.getenv('POSTGRES_HOST','db')
#port=int(os.getenv('POSTGRES_PORT','5432'))
#user=os.getenv('POSTGRES_USER','postgres')
#password=os.getenv('POSTGRES_PASSWORD','')
#db=os.getenv('POSTGRES_DB','postgres')
#for i in range(60):
#    try:
#        psycopg2.connect(host=host, port=port, user=user, password=password, dbname=db).close()
#        print('Database is up!')
#        break
#    except Exception as e:
#        print('Waiting for database...', e)
#        time.sleep(2)
#else:
#    print('Database connection timeout', file=sys.stderr)
#    sys.exit(1)
#PY

python manage.py makemigrations --noinput || true
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Start ASGI server via gunicorn uvicorn workers
exec gunicorn fresh_cart.asgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-logfile '-' \
    --error-logfile '-' \
    --timeout 120
