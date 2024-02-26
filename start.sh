#!/bin/bash
set -e

# Start Redis in the background
redis-server --daemonize yes

# Start Celery worker in the background
celery -A app.celery worker --loglevel=info --concurrency=4 &

# Start Nginx in the background
nginx -g 'daemon on;'

# Start the Flask application with Gunicorn on the Cloud Run port
exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
