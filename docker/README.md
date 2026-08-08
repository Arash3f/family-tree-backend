# Docker

All container build and Compose definitions live in this folder.

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage image for API / Celery / Flower |
| `entrypoint.sh` | Wait for Postgres → migrate → start Uvicorn |
| `compose.full.yml` | Full stack (app + Postgres + Redis + Neo4j) |
| `compose.app.yml` | App containers only (host infra via `host.docker.internal`) |
| `compose.app.with-infra.yml` | Overlay: join full-stack `family-tree-net` |
| `compose.ci-local.yml` | Alternate host ports for local CI simulation |

Run every command from the **repository root**.

## Prerequisites

```bash
cp .env.example .env
# JWT_SECRET must be at least 32 characters
```

## Full stack

```bash
docker compose -f docker/compose.full.yml --env-file .env up --build
```

Uses Docker DNS names from `.env.example` (`db`, `redis`, `neo4j`).

## App only

Infra must already be running (host or Compose).

**Host infra:**

```bash
docker compose -f docker/compose.app.yml --env-file .env up --build
```

**Compose infra** (`db`/`redis`/`neo4j` from `compose.full.yml`):

```bash
docker compose -f docker/compose.full.yml --env-file .env up -d db redis neo4j

# PowerShell example
$env:APP_POSTGRES_HOST="db"
$env:APP_CELERY_BROKER_URL="redis://redis:6379/0"
$env:APP_CELERY_RESULT_BACKEND="redis://redis:6379/1"
$env:APP_NEO4J_URI="bolt://neo4j:7687"

docker compose -f docker/compose.app.yml -f docker/compose.app.with-infra.yml --env-file .env up --build
```

## CI-local ports

```bash
docker compose -f docker/compose.full.yml -f docker/compose.ci-local.yml --env-file .env up --build
```

## Useful commands

```bash
# Stop full stack and remove volumes
docker compose -f docker/compose.full.yml --env-file .env down -v

# Logs
docker compose -f docker/compose.full.yml --env-file .env logs -f api

# Shell into API
docker compose -f docker/compose.full.yml --env-file .env exec api sh
```

## Published ports (defaults)

| Service | Port |
|---------|------|
| API (REST + GraphQL) | `8001` |
| GraphQL / GraphiQL | `http://localhost:8001/graphql` |
| Flower | `5555` |
| Postgres | `5432` |
| Redis | `6379` |
| Neo4j Browser / Bolt | `7474` / `7687` |

Override with `API_PORT`, `FLOWER_PORT`, `POSTGRES_PUBLISH_PORT`, `REDIS_PUBLISH_PORT`, `NEO4J_HTTP_PORT`, `NEO4J_BOLT_PORT` in `.env` or the shell.
