"""
Production-ready WSGI configuration for gunicorn
"""
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 60

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'aksjeradar'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None

# Debugging
reload = False
reload_engine = 'auto'
spew = False

# Server hooks
def when_ready(server):
    server.log.info("Server is ready. Doing nothing.")

def on_exit(server):
    server.log.info("Server is stopping. Doing nothing.")
