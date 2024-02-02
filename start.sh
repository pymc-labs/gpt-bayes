#!/bin/bash
set -e

# Start Redis in the background
redis-server --daemonize yes

# Start Celery worker in the background
celery -A app.celery worker --loglevel=info --concurrency=1 &

# Start the Flask application
exec gunicorn --bind :5000 --workers 1 --threads 8 --timeout 0 app:app
