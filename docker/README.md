# Docker

All container build and Compose definitions live in this folder.

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage: `runtime` (prod) and `ci` (tests/tooling); Compose builds `ci` |
| `entrypoint.sh` | Wait for Postgres → migrate → start Uvicorn |
| `compose.yml` | Full stack (app + Postgres + Redis + Neo4j + MinIO) |
| `compose.host-ports.yml` | Optional publish of DB/Redis/Neo4j/MinIO ports to the host |

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

By default only **API** (`8001`) and **Flower** (`5555`) are published on the host.
Postgres / Redis / Neo4j / MinIO stay on the Compose network. For host tools
(psql, Neo4j Browser, MinIO console):

```bash
docker compose -f docker/compose.yml -f docker/compose.host-ports.yml --env-file .env up -d
```

MinIO starts with a private bucket (`MINIO_BUCKET`, default `family-tree`). The API
uses `MINIO_ENDPOINT` inside Docker and signs download URLs with
`MINIO_PUBLIC_ENDPOINT` (host-reachable, e.g. `localhost:9000` — requires host ports).

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
DB_USER="$(grep '^POSTGRES_USER=' .env | cut -d '=' -f2)"
DB_TEST="$(grep '^POSTGRES_DB_TEST=' .env | cut -d '=' -f2)"
docker compose -f docker/compose.yml --env-file .env exec -T db \
  psql -U "$DB_USER" -tc "SELECT 1 FROM pg_database WHERE datname = '${DB_TEST}'" | grep -q 1 \
  || docker compose -f docker/compose.yml --env-file .env exec -T db \
      psql -U "$DB_USER" -c "CREATE DATABASE ${DB_TEST}"

docker compose -f docker/compose.yml --env-file .env exec -T api \
  pytest -v --cov=app --cov-fail-under=55
```

## Published ports (defaults)

| Service | Port | Published by default? |
|---------|------|------------------------|
| API (REST + GraphQL) | `8001` | yes |
| GraphQL / GraphiQL | `http://localhost:8001/graphql` | yes |
| Flower | `5555` | yes |
| Postgres | `5432` | only with `compose.host-ports.yml` |
| Redis | `6379` | only with `compose.host-ports.yml` |
| Neo4j Browser / Bolt | `7474` / `7687` | only with `compose.host-ports.yml` |
| MinIO API / Console | `9000` / `9001` | only with `compose.host-ports.yml` |

Override mapped host ports with `API_PORT`, `FLOWER_PORT`, `POSTGRES_PUBLISH_PORT`,
`REDIS_PUBLISH_PORT`, `NEO4J_HTTP_PORT`, `NEO4J_BOLT_PORT`, `MINIO_API_PORT`,
`MINIO_CONSOLE_PORT` in `.env` or the shell.
