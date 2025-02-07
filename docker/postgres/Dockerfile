###############################
# Stage 1: Builder
###############################
FROM postgres:17 AS builder

# Build-time configurations
ARG POSTGRES_USER=clonehero
ARG POSTGRES_PASSWORD=clonehero
ARG POSTGRES_DB=clonehero

# Set up environment variables
ENV POSTGRES_USER=${POSTGRES_USER} \
    POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
    POSTGRES_DB=${POSTGRES_DB}

# Create a directory for custom initialization scripts
RUN mkdir -p /docker-entrypoint-initdb.d

# Copy any custom initialization scripts (if any)
# COPY init-scripts/*.sql /docker-entrypoint-initdb.d/

# Expose PostgreSQL port
EXPOSE 5432


###############################
# Stage 2: Runtime
###############################
FROM postgres:17

# Copy the prepared initialization files from builder stage
COPY --from=builder /docker-entrypoint-initdb.d /docker-entrypoint-initdb.d

# Create a non-root user for better security
RUN mkdir -p /var/lib/postgresql \
    && chown -R postgres:postgres /var/lib/postgresql /docker-entrypoint-initdb.d

# Switch to non-root user
USER postgres

# Set health check to ensure DB is ready
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" || exit 1

# Default command
CMD ["postgres"]