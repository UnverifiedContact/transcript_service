#!/bin/bash

# Absolute path to the directory containing THIS script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Relative paths from the script location
VENV="$SCRIPT_DIR/venv"
APP_DIR="$SCRIPT_DIR"

PIDFILE="$SCRIPT_DIR/app.pid"
LOGDIR="$SCRIPT_DIR/logs"
LOGFILE="$LOGDIR/app.log"

mkdir -p "$LOGDIR"

# Already running?
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    #echo "transcript-service is already running on PID $(cat "$PIDFILE")"
    exit 0
fi

# Load environment variables if .env exists
if [ -f "$APP_DIR/.env" ]; then
    export $(cat "$APP_DIR/.env" | grep -v '^#' | xargs)
fi

# Set defaults
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-"5485"}
export GUNICORN_WORKERS=${GUNICORN_WORKERS:-"1"}
export GUNICORN_THREADS=${GUNICORN_THREADS:-"4"}
export GUNICORN_LOG_LEVEL=${GUNICORN_LOG_LEVEL:-"info"}
export GUNICORN_RELOAD=${GUNICORN_RELOAD:-"0"}

nohup "$VENV/bin/gunicorn" \
    --chdir "$APP_DIR" \
    --bind "$HOST:$PORT" \
    --workers "$GUNICORN_WORKERS" \
    --worker-class gthread \
    --threads "$GUNICORN_THREADS" \
    --timeout 60 \
    --max-requests 500 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    --log-level "$GUNICORN_LOG_LEVEL" \
    --limit-request-line 4094 \
    --limit-request-fields 100 \
    --limit-request-field_size 8190 \
    --preload \
    app:app \
    >>"$LOGFILE" 2>&1 &

echo $! > "$PIDFILE"
