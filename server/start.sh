#!/bin/bash
set -e

# Start Redis in the background with specific directory configurations
redis-server --daemonize yes \
    --dir /opt/conda/var/db/redis \
    --logfile /opt/conda/var/db/redis/redis.log \
    --pidfile /opt/conda/var/db/redis/redis.pid

# Start Celery worker in the background
celery -A app.celery worker --loglevel=debug --concurrency=4 &
# celery -A app.celery worker --loglevel=debug --concurrency=4 &

# Start the Flask application with Gunicorn on the Cloud Run port
exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 --log-level debug app:app
