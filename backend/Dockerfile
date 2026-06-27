# ─── ThreatMind AI backend image (multi-stage) ───
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps for asyncpg/cryptography builds.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# ─── Builder: install deps ───
FROM base AS builder
COPY pyproject.toml ./
COPY app ./app
RUN pip install --prefix=/install -e .

# ─── Runtime ───
FROM base AS runtime
# Create a non-root user.
RUN useradd --create-home --uid 10001 appuser
COPY --from=builder /install /usr/local
COPY . .
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/v1/health/live || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
