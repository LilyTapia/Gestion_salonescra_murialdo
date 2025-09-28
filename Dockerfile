# Dockerfile for Django + MySQL (dev)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=off     PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app

# System deps for mysqlclient
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    gcc \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install deps first (better caching)
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Copy project
COPY . /app

# Create a non-root user (optional)
RUN useradd -ms /bin/bash appuser
USER appuser

# Entrypoint waits for DB, runs migrations, seeds and starts server
ENTRYPOINT ["/app/entrypoint.sh"]
