# Docker

All container build and Compose definitions live in this folder.

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage image for API / Celery / Flower (`postgresql-client` for backups) |
| `entrypoint.sh` | Wait for Postgres → migrate → start Uvicorn |
| `compose.yml` | Full stack (app + Postgres + Redis + Neo4j + MinIO) |

Run every command from the **repository root**.

## Prerequisites

```bash
cp .env.example .env
# JWT_SECRET must be at least 32 characters
```

## Start

```bash
docker compose -f docker/compose.yml --env-file .env up --build
```

Uses Docker DNS names from `.env.example` (`db`, `redis`, `neo4j`, `minio`).

MinIO starts with a private bucket (`MINIO_BUCKET`, default `family-tree`). The API
uses `MINIO_ENDPOINT` inside Docker and signs download URLs with
`MINIO_PUBLIC_ENDPOINT` (host-reachable, e.g. `localhost:9000`).

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

| Service | Port |
|---------|------|
| API (REST + GraphQL) | `8001` |
| GraphQL / GraphiQL | `http://localhost:8001/graphql` |
| Flower | `5555` (basic auth: `FLOWER_BASIC_AUTH`) |
| Postgres | `5432` |
| Redis | `6379` |
| Neo4j Browser / Bolt | `7474` / `7687` |
| MinIO API / Console | `9000` / `9001` |

Override with `API_PORT`, `FLOWER_PORT`, `POSTGRES_PUBLISH_PORT`, `REDIS_PUBLISH_PORT`, `NEO4J_HTTP_PORT`, `NEO4J_BOLT_PORT`, `MINIO_API_PORT`, `MINIO_CONSOLE_PORT` in `.env` or the shell.
