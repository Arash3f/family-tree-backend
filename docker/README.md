# Docker

All container build and Compose definitions live in this folder.

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage image for API / Celery / Flower (`postgresql-client` for backups) |
| `entrypoint.sh` | Wait for Postgres → migrate → start Uvicorn |
| `compose.yml` | Full stack (app + Postgres + Redis + Neo4j) |

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

Uses Docker DNS names from `.env.example` (`db`, `redis`, `neo4j`).

## Useful commands

```bash
# Stop and remove volumes
docker compose -f docker/compose.yml --env-file .env down -v

# Logs
docker compose -f docker/compose.yml --env-file .env logs -f api

# Shell into API
docker compose -f docker/compose.yml --env-file .env exec api sh

# Tests inside the API container (after stack is up)
docker compose -f docker/compose.yml --env-file .env exec -T api pytest -v --cov=app --cov-fail-under=50
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

Override with `API_PORT`, `FLOWER_PORT`, `POSTGRES_PUBLISH_PORT`, `REDIS_PUBLISH_PORT`, `NEO4J_HTTP_PORT`, `NEO4J_BOLT_PORT` in `.env` or the shell.
