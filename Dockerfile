# Dockerfile — Noventra platform (Phase 3 skeleton).
# Per ADR-0022 / DEC-0027: pinned Python 3.11-slim, non-root user,
# src-layout install.

FROM python:3.11-slim AS base

# System deps for psycopg (libpq) and redis (no extra deps needed).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer caching).
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .[dev]

# Copy the rest of the project.
COPY . .

# Non-root user for runtime.
RUN useradd -m -u 1000 noventra && chown -R noventra:noventra /app
USER noventra

ENV DJANGO_SETTINGS_MODULE=noventra.settings.production
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Healthcheck: hit the /health/ endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Default: gunicorn production server.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "noventra.wsgi:application"]
