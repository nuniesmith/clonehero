###############################
# Stage 1: Builder
###############################
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies needed to compile any native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a Python virtual environment
RUN python -m venv /opt/venv

# Copy backend-specific requirements and install them into the virtual environment
COPY requirements.txt /app/requirements.txt
RUN /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy the backend application code
COPY . /app

###############################
# Stage 2: Runtime
###############################
FROM python:3.13-slim

# Runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install runtime dependencies (if any additional packages are needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a dedicated non-root user before setting ownership
RUN useradd -m appuser

# Copy the virtual environment and the application code from the builder stage
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

# Ensure necessary directories exist and set proper ownership
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Expose port for healthcheck consistency
EXPOSE 8001

# Health Check: Ensure the backend is responding
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8001/health || exit 1

# Switch to the non-root user
USER appuser

# Set the working directory to the backend code folder
WORKDIR /app

# Default Entrypoint
CMD ["/opt/venv/bin/python", "src/backend/worker.py"]