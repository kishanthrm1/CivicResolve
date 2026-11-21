# CivicResolve - Production Dockerfile for Google Cloud Run
FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr and writing bytecode
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Create uploads directory and set permissions
RUN mkdir -p /app/static/uploads && chmod -R 777 /app/static/uploads

# Create non-root user for enhanced container security
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

# Expose default Cloud Run container port
EXPOSE 8080

# Run with Gunicorn WSGI server binding to $PORT
CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 120 "app:create_app()"
