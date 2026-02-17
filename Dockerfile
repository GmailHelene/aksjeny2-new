# Use Python 3.10 slim as base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Configure apt to retry downloads
RUN echo 'Acquire::Retries "3";' > /etc/apt/apt.conf.d/80-retries

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    wget \
    pkg-config \
    git \
    make \
    automake \
    autoconf \
    libtool \
    libssl-dev \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create ta-lib.conf for ldconfig
RUN echo "/usr/lib" > /etc/ld.so.conf.d/ta-lib.conf

# Copy requirements and installation scripts
COPY requirements.txt install_talib.sh ./
RUN chmod +x install_talib.sh

# Upgrade pip
RUN pip install --upgrade pip

# Install TA-Lib
RUN ./install_talib.sh

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure start script is executable
RUN chmod +x ./start.sh

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV TA_LIBRARY_PATH=/usr/lib
ENV TA_INCLUDE_PATH=/usr/include/ta-lib

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Expose port (Cloud Run expects the container to listen on $PORT, default 8080)
EXPOSE 8080

# Health check (for local/docker usage). Cloud Run ignores Dockerfile HEALTHCHECK.
HEALTHCHECK --interval=30s --timeout=30s --start-period=20s --retries=3 CMD curl -fsS http://localhost:8080/health/ready || exit 1

# Use Gunicorn with the WSGI app for production
ENV GUNICORN_WORKERS=2
ENV GUNICORN_THREADS=4
ENV GUNICORN_TIMEOUT=120

# Force threading mode for SocketIO to avoid eventlet/gevent in container if not configured
ENV SOCKETIO_FORCE_THREADING=1

# Run via start script (expands $PORT) for portability across platforms
CMD ["/bin/sh", "-c", "./start.sh"]
