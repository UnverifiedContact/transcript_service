#!/bin/bash

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set defaults
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-"5485"}
export GUNICORN_WORKERS=${GUNICORN_WORKERS:-"4"}
export GUNICORN_LOG_LEVEL=${GUNICORN_LOG_LEVEL:-"info"}
export GUNICORN_RELOAD=${GUNICORN_RELOAD:-"0"}

gunicorn \
    --bind "$HOST:$PORT" \
    --workers "$GUNICORN_WORKERS" \
    --worker-class eventlet \
    --timeout 30 \
    --max-requests 500 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    --log-level "$GUNICORN_LOG_LEVEL" \
    --preload \
    app:app
