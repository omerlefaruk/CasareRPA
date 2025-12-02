# CasareRPA Unified Multi-Stage Dockerfile
# Build different image variants using --target flag:
#   docker build --target orchestrator -t casare-orchestrator .
#   docker build --target robot -t casare-robot .
#   docker build --target robot-headless -t casare-robot-headless .
#
# BuildKit features enabled for better caching:
#   DOCKER_BUILDKIT=1 docker build ...

# =============================================================================
# Stage: Base Python (shared foundation)
# =============================================================================
FROM python:3.12-slim AS python-base

# Metadata
LABEL org.opencontainers.image.vendor="CasareRPA"
LABEL org.opencontainers.image.source="https://github.com/casarerpa/casarerpa"
LABEL maintainer="CasareRPA Team"

# Common environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# =============================================================================
# Stage: Builder (compile dependencies)
# =============================================================================
FROM python-base AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy dependency files first (layer caching)
COPY pyproject.toml ./
COPY src/ ./src/

# Install package with all dependencies
RUN pip install --upgrade pip && \
    pip install .

# =============================================================================
# Stage: Builder Minimal (for cloud deployments with lighter deps)
# =============================================================================
FROM python-base AS builder-minimal

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy minimal requirements
COPY deploy/orchestrator/requirements.txt ./requirements.txt

# Install only required dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application source
COPY src/casare_rpa/ /build/casare_rpa/

# =============================================================================
# Stage: Orchestrator (FastAPI API server)
# =============================================================================
FROM python-base AS orchestrator

LABEL org.opencontainers.image.title="CasareRPA Orchestrator"
LABEL org.opencontainers.image.description="Robot fleet management and job orchestration API"
LABEL org.opencontainers.image.version="3.0.0"

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r casare && useradd -r -g casare -s /bin/bash casare \
    && mkdir -p /app/data && chown -R casare:casare /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=casare:casare src/casare_rpa/ /app/casare_rpa/

# Application environment
ENV PYTHONPATH=/app \
    CASARE_ENV=production \
    CASARE_LOG_LEVEL=INFO \
    HOST=0.0.0.0 \
    PORT=8000 \
    WORKERS=4

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Switch to non-root user
USER casare

# Run orchestrator
CMD ["sh", "-c", "uvicorn casare_rpa.infrastructure.orchestrator.api.main:app --host $HOST --port $PORT --workers $WORKERS"]

# =============================================================================
# Stage: Orchestrator Cloud (lighter for Railway/Render/Fly)
# =============================================================================
FROM python-base AS orchestrator-cloud

LABEL org.opencontainers.image.title="CasareRPA Cloud Orchestrator"
LABEL org.opencontainers.image.description="Lightweight orchestrator for cloud deployment"
LABEL org.opencontainers.image.version="3.0.0"

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r casare && useradd -r -g casare -s /bin/bash casare

# Copy virtual environment from minimal builder
COPY --from=builder-minimal /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --from=builder-minimal --chown=casare:casare /build/casare_rpa/ /app/casare_rpa/

# Application environment
ENV PYTHONPATH=/app \
    HOST=0.0.0.0 \
    PORT=8000 \
    WORKERS=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

USER casare

CMD ["sh", "-c", "python -m uvicorn casare_rpa.infrastructure.orchestrator.server:app --host $HOST --port $PORT"]

# =============================================================================
# Stage: Robot Base (shared robot foundation)
# =============================================================================
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy AS robot-base

LABEL org.opencontainers.image.vendor="CasareRPA"

WORKDIR /build

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install dependencies
COPY pyproject.toml ./
COPY src/ ./src/

RUN pip install --upgrade pip && \
    pip install .

# =============================================================================
# Stage: Robot (full browser automation with all browsers)
# =============================================================================
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy AS robot

LABEL org.opencontainers.image.title="CasareRPA Browser Robot"
LABEL org.opencontainers.image.description="Full browser automation robot with Chromium, Firefox, WebKit"
LABEL org.opencontainers.image.version="3.0.0"

WORKDIR /app

# Create non-root user
RUN useradd -m -s /bin/bash robot && \
    mkdir -p /home/robot/.cache /app/data && \
    chown -R robot:robot /home/robot /app

# Copy virtual environment from robot-base
COPY --from=robot-base /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=robot:robot src/casare_rpa/ /app/casare_rpa/

# Install all browsers
RUN playwright install chromium firefox webkit && \
    chown -R robot:robot /ms-playwright

# Application environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    CASARE_ENV=production \
    CASARE_LOG_LEVEL=INFO \
    CASARE_ROBOT_TYPE=browser \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health', timeout=5)" || exit 1

USER robot

VOLUME ["/home/robot/.cache", "/app/data"]

CMD ["python", "-m", "casare_rpa.robot.distributed_agent"]

# =============================================================================
# Stage: Robot Headless (Chromium only, smaller image)
# =============================================================================
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy AS robot-headless

LABEL org.opencontainers.image.title="CasareRPA Headless Robot"
LABEL org.opencontainers.image.description="Lightweight headless browser robot with Chromium only"
LABEL org.opencontainers.image.version="3.0.0"

WORKDIR /app

# Create non-root user
RUN useradd -m -s /bin/bash robot && \
    mkdir -p /home/robot/.cache /app/data && \
    chown -R robot:robot /home/robot /app

# Copy virtual environment from robot-base
COPY --from=robot-base /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=robot:robot src/casare_rpa/ /app/casare_rpa/

# Install only Chromium (smaller image)
RUN playwright install chromium && \
    chown -R robot:robot /ms-playwright

# Application environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    CASARE_ENV=production \
    CASARE_LOG_LEVEL=INFO \
    CASARE_ROBOT_TYPE=browser \
    CASARE_BROWSER=chromium \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health', timeout=5)" || exit 1

USER robot

VOLUME ["/home/robot/.cache", "/app/data"]

CMD ["python", "-m", "casare_rpa.robot.distributed_agent"]

# =============================================================================
# Stage: Development (all tools for local development)
# =============================================================================
FROM python-base AS development

LABEL org.opencontainers.image.title="CasareRPA Development"
LABEL org.opencontainers.image.description="Development environment with all tools"

WORKDIR /app

# Install all development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libpq5 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install development dependencies
RUN pip install pytest pytest-asyncio pytest-cov ruff mypy

# Copy application code
COPY src/casare_rpa/ /app/casare_rpa/
COPY tests/ /app/tests/
COPY pyproject.toml /app/

ENV PYTHONPATH=/app \
    CASARE_ENV=development

# No healthcheck for dev - manual control
EXPOSE 8000 8080

CMD ["python", "-m", "pytest", "tests/", "-v"]
