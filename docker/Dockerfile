# syntax=docker/dockerfile:1

FROM python:3.11.15-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# curl: HEALTHCHECK / Flower probes; postgresql-client: pg_dump for Celery backups
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
FROM base AS builder-runtime

COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# ---------------------------------------------------------------------------
FROM base AS builder-ci

COPY requirements.txt requirements-dev.txt ./
RUN pip install --prefix=/install -r requirements.txt \
    && pip install --prefix=/install -r requirements-dev.txt

# ---------------------------------------------------------------------------
FROM base AS runtime

RUN groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --create-home --home-dir /home/app app

COPY --from=builder-runtime /install /usr/local

COPY --chown=app:app . .
COPY --chown=app:app docker/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh \
    && chmod +x /entrypoint.sh \
    && mkdir -p /mnt/backups /app/celerybeat \
    && chown -R app:app /app /mnt/backups /app/celerybeat

USER app

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8001/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

# ---------------------------------------------------------------------------
# Local/CI image: the runtime image plus pytest and the linters, so the suite
# runs against the same layers that ship to production.
FROM runtime AS ci

USER root
COPY --from=builder-ci /install /usr/local
USER app
