# Docker

All container build and Compose definitions live in this folder.

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage: `runtime` (prod) and `ci` (= `runtime` + pytest/linters) |
| `entrypoint.sh` | Wait for Postgres → migrate → start Uvicorn |
| `compose.yml` | Full stack (app + Postgres + Redis + Neo4j + MinIO) |
| `compose.host-ports.yml` | Optional publish of DB/Redis/Neo4j/MinIO ports to the host |
| `compose.source-mount.yml` | Run containers against the working tree instead of the baked-in code |

Run every command from the **repository root**.

## Prerequisites

```bash
cp .env.example .env
# JWT_SECRET must be at least 32 characters
# Keep ENVIRONMENT=local for demo passwords; staging/production reject weak defaults
```

## Start

```bash
docker compose -f docker/compose.yml --env-file .env up --build
```

Uses Docker DNS names from `.env.example` (`db`, `redis`, `neo4j`, `minio`).

## Choosing the image

Compose builds the `runtime` stage, which contains only production dependencies.
Set `APP_IMAGE_TARGET=ci` (in `.env` or the shell) to build the `ci` stage instead —
the same image plus pytest, Ruff, mypy, and Bandit — which is what you need to run
the suite inside the container. Images are tagged per target
(`family-tree-api:runtime`, `family-tree-api:ci`), so switching never reuses a stale
image.

```bash
APP_IMAGE_TARGET=ci docker compose -f docker/compose.yml --env-file .env up -d --build
```

By default only **API** (`8001`) is published on the host.
Postgres / Redis / Neo4j / MinIO stay on the Compose network. For host tools
(psql, Neo4j Browser, MinIO console):

```bash
docker compose -f docker/compose.yml -f docker/compose.host-ports.yml --env-file .env up -d
```

MinIO buckets listed in `MINIO_BUCKETS` (comma-separated; default follows `MINIO_BUCKET`,
usually `family-tree`) are created on API startup if missing. `MINIO_BUCKET` is the
primary bucket for person photos. The API talks to MinIO on the Compose network
(`MINIO_ENDPOINT`). Person photos are served through `GET /media/{object_key}` so the
browser never needs MinIO host ports.

Celery worker/beat run as the image `app` user (uid 1000) and wait until `api` is
healthy (so Alembic migrations finish first). If an old `backup_data` /
`celerybeat_data` volume was created as root, recreate it once:
`docker compose -f docker/compose.yml --env-file .env down -v` (destructive).

## Useful commands

```bash
# Stop and remove volumes
docker compose -f docker/compose.yml --env-file .env down -v

# Logs
docker compose -f docker/compose.yml --env-file .env logs -f api

# Shell into API
docker compose -f docker/compose.yml --env-file .env exec api sh

# Create the test database (required once per Postgres volume), then run pytest
# (needs APP_IMAGE_TARGET=ci)
DB_USER="$(grep '^POSTGRES_USER=' .env | cut -d '=' -f2)"
DB_TEST="$(grep '^POSTGRES_DB_TEST=' .env | cut -d '=' -f2)"
docker compose -f docker/compose.yml --env-file .env exec -T db \
  psql -U "$DB_USER" -tc "SELECT 1 FROM pg_database WHERE datname = '${DB_TEST}'" | grep -q 1 \
  || docker compose -f docker/compose.yml --env-file .env exec -T db \
      psql -U "$DB_USER" -c "CREATE DATABASE ${DB_TEST}"

docker compose -f docker/compose.yml --env-file .env exec -T api \
  pytest -v --cov=app --cov-fail-under=80
```

## Published ports (defaults)

| Service | Port | Published by default? |
|---------|------|------------------------|
| API (REST + GraphQL) | `8001` | yes |
| GraphQL / GraphiQL | `http://localhost:8001/graphql` | yes |
| Postgres | `5432` | only with `compose.host-ports.yml` |
| Redis | `6379` | only with `compose.host-ports.yml` |
| Neo4j Browser / Bolt | `7474` / `7687` | only with `compose.host-ports.yml` |
| MinIO API / Console | `9000` / `9001` | only with `compose.host-ports.yml` |

Override mapped host ports with `API_PORT`, `POSTGRES_PUBLISH_PORT`,
`REDIS_PUBLISH_PORT`, `NEO4J_HTTP_PORT`, `NEO4J_BOLT_PORT`, `MINIO_API_PORT`,
`MINIO_CONSOLE_PORT` in `.env` or the shell.
