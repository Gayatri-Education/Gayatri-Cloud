# Multi-stage production Dockerfile for Gayatri Cloud Backend (FastAPI)
# Target architecture: Linux x86_64 / arm64

# --- Stage 1: Build & Dependency Wheel Cache ---
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml ./

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Minimal Production Runtime ---
FROM python:3.12-slim AS runner

LABEL maintainer="Gayatri Education <support@gayatri.internal>"
LABEL description="Gayatri Cloud Backend API Server"

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root system user and group (UID 10001)
RUN groupadd -g 10001 backendgroup && \
    useradd -u 10001 -g backendgroup -s /bin/bash -m backenduser

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy backend application source
COPY --chown=backenduser:backendgroup . /app/

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    APP_ENV=production

# Switch to non-root user
USER 10001:10001

EXPOSE 8000

# Container readiness healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/ready || exit 1

# Production ASGI server with 4 worker processes
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
