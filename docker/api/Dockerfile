###############################
# Stage 1: Builder
###############################
FROM python:3.13-slim AS builder

WORKDIR /app

# Install system dependencies needed to build packages (e.g. psycopg2) and any other build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment for installing Python dependencies
RUN python -m venv /opt/venv

# Copy API-specific requirements and install them into the virtual environment
COPY requirements.txt /app/requirements.txt
RUN /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy the API application code
COPY . /app

###############################
# Stage 2: Runtime
###############################
FROM python:3.13-slim

# Environment variables for runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install only runtime system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment and the application code from the builder stage
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

# Create a dedicated non-root user and adjust permissions
RUN useradd -m appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Expose the API port
EXPOSE 8000

# Health Check: Ensure the API is responding on port 8000.
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

# Switch to the non-root user
USER appuser

# Set the working directory for running the API service
WORKDIR /app

# Default Entrypoint: Start Gunicorn with Uvicorn workers for the API
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "src.main:app"]