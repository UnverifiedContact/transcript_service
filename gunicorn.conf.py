#!/usr/bin/env python3
"""
Gunicorn configuration file for YouTube Transcript Service
Production-ready settings optimized for 10-20 parallel requests
"""

import os
import multiprocessing
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Server socket
bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '5485')}"
backlog = 2048

# Worker processes - optimized for Helio G99 mobile deployment
workers = int(os.getenv('GUNICORN_WORKERS', 4))  # Conservative for mobile: 4 workers
worker_class = "gevent"  # Async workers for better mobile performance
threads = 2  # 2 threads per worker for I/O-bound tasks
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to prevent memory leaks (lower for mobile)
max_requests = 500
max_requests_jitter = 50

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'youtube-transcript-service'

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment if needed)
# keyfile = None
# certfile = None

# Worker process management
preload_app = True
reload = os.getenv('GUNICORN_RELOAD', '0') in ('1', 'true', 'yes', 'on')

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
