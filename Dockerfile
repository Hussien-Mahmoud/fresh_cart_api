# Python base image
FROM python:3.13

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (no supervisor)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    nginx \
    redis-server \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Nginx config
RUN mkdir -p /var/log/nginx /run/nginx /etc/nginx/conf.d \
 && rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf || true \
 && cp /app/nginx.conf /etc/nginx/conf.d/default.conf

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Expose HTTP
EXPOSE 80

# Copy env file into image (can also be mounted at runtime)
COPY .env /app/.env

# Use tini as PID 1 and run our entrypoint orchestrator
ENTRYPOINT ["/usr/bin/tini", "--", "/app/entrypoint.sh"]
