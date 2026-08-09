# Family Tree API

Production-oriented backend for managing family trees: people, marriages, and graph relationships.

Built with **FastAPI** and **Clean Architecture**. Exposes both **REST** and **GraphQL** APIs over the same use cases. **PostgreSQL** is the source of truth for transactional data; **Neo4j** stores parent/spouse edges for traversals such as shortest-path (closest relationship) queries. Person photos are stored in **MinIO** (private bucket + presigned URLs). Background work runs on **Celery** + **Redis**.

| | |
|---|---|
| **Version** | `0.1.0` |
| **Python** | `3.11+` |
| **License** | MIT |

---

## Table of contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Quick start (Docker)](#quick-start-docker)
- [Local development](#local-development)
- [Configuration](#configuration)
- [API overview](#api-overview)
- [GraphQL API](#graphql-api)
- [Authentication & authorization](#authentication--authorization)
- [Background jobs](#background-jobs)
- [Testing & quality](#testing--quality)
- [CI / GitHub Actions](#ci--github-actions)
- [Project layout](#project-layout)
- [API client (Bruno)](#api-client-bruno)
- [Seeding sample data](#seeding-sample-data)
- [Known limitations](#known-limitations)
- [Roadmap](#roadmap)

---

## Features

- Hybrid persistence: PostgreSQL (CRUD, auth, history) + Neo4j (graph edges & path queries)
- Dual API surface: REST routers + GraphQL (Strawberry) sharing the same application layer
- Closest relationship between two people: REST `GET /persons/{from_id}/relation/{to_id}` or GraphQL `closestRelationship`
- JWT auth with access + refresh tokens (same tokens for REST and GraphQL)
- Role-based access control (permissions on roles)
- Async SQLAlchemy + Alembic migrations
- Celery sync of person/marriage changes into Neo4j after commit
- Scheduled database backups via Celery Beat
- Docker stack under `docker/` (Compose full stack; multi-stage image)
- Bruno collection for manual REST API testing
- CI: Ruff, mypy, Bandit, Docker stack + Pytest (GitHub Actions)

---

## Architecture

```
┌──────────────────────┐     ┌──────────────────┐     ┌─────────────┐
│ FastAPI              │────▶│  Use cases /     │────▶│ PostgreSQL  │
│  REST + GraphQL      │     │  domain services │     │ (source of  │
└──────────────────────┘     └────────┬─────────┘     │  truth)     │
                                      │               └─────────────┘
                                      │ commit OK
                                      ▼
                             ┌──────────────────┐     ┌─────────────┐
                             │ Celery (Redis)   │────▶│   Neo4j     │
                             │ sync + backup    │     │ (graph)     │
                             └──────────────────┘     └─────────────┘
```

### Layers

| Layer | Responsibility |
|--------|----------------|
| **Presentation** | REST routers + GraphQL schema/resolvers, Pydantic/Strawberry schemas, auth/permission guards, mappers |
| **Application** | Use cases, DTOs, authorization & graph-sync services |
| **Domain** | Entities, invariants, repository ports, marriage rules |
| **Infrastructure** | SQLAlchemy, Neo4j client, JWT/Argon2, Unit of Work, Celery |
| **Celery** | Person/relationship sync tasks, scheduled backups |

REST and GraphQL both call the same use cases and permission checks; they stay behaviorally in sync.

### Data ownership

| Store | Owns |
|--------|------|
| PostgreSQL | Users, roles, permissions, persons, marriages (including divorce history) |
| Neo4j | `Person` nodes, `PARENT_OF` / `SPOUSE_OF` relationships for traversal |

After a successful Postgres commit, the application enqueues Celery tasks to mirror relevant changes in Neo4j.

---

## Tech stack

| Area | Choice |
|------|--------|
| API | FastAPI, Uvicorn, Strawberry GraphQL |
| ORM / DB | SQLAlchemy 2 (async), asyncpg, Alembic, PostgreSQL 15 (Compose) |
| Graph | Neo4j 5 |
| Queue | Celery, Redis 8 (Compose), Flower |
| Auth | OAuth2 password flow, JWT (`python-jose`), Argon2 (`passlib`) |
| Validation | Pydantic v2 |
| Quality | Ruff, mypy, Bandit, pre-commit, Commitizen, Pytest |
| CI | GitHub Actions (see [CI / GitHub Actions](#ci--github-actions)) |

---

## Quick start (Docker)

**Requirements:** Docker and Docker Compose.

Run every command from the **backend repository root** (this folder). All Docker assets live under [`docker/`](docker/README.md).

```bash
cp .env.example .env
# Edit .env if needed. JWT_SECRET must be at least 32 characters.
```

### Start the stack

Starts API, Celery worker/beat, Flower, Postgres, Redis, Neo4j, and MinIO.

```bash
docker compose -f docker/compose.yml --env-file .env up --build
```

`.env.example` already uses Docker DNS names (`db`, `redis`, `neo4j`).

The API entrypoint waits for Postgres, runs `alembic upgrade head`, then starts Uvicorn. Compose Celery workers use the default pool (not `--pool=solo`); use solo only for host processes on Windows — see [Local development](#6-celery-worker-and-beat).

```bash
# Stop and remove volumes
docker compose -f docker/compose.yml --env-file .env down -v

# Logs / shell
docker compose -f docker/compose.yml --env-file .env logs -f api
docker compose -f docker/compose.yml --env-file .env exec api sh
```

| Service | URL / port |
|---------|------------|
| API | http://localhost:8001 |
| Swagger UI | http://localhost:8001/api_docs |
| ReDoc | http://localhost:8001/redoc |
| OpenAPI JSON | http://localhost:8001/openapi.json |
| GraphQL (GraphiQL) | http://localhost:8001/graphql |
| Health | http://localhost:8001/health (HTTP 200 when ok, 503 when degraded) |
| Flower | http://localhost:5555 (basic auth from `FLOWER_BASIC_AUTH`, default `admin:admin`) |

DB / Redis / Neo4j / MinIO ports are **not** published by default. For host access
(Neo4j Browser, MinIO console, psql):

```bash
docker compose -f docker/compose.yml -f docker/compose.host-ports.yml --env-file .env up -d
```

Then: Neo4j Browser `http://localhost:7474`, MinIO `http://localhost:9000` /
`http://localhost:9001`.

Override published ports with `API_PORT`, `FLOWER_PORT`, and (with host-ports file)
`POSTGRES_PUBLISH_PORT`, `REDIS_PUBLISH_PORT`, `NEO4J_HTTP_PORT`, `NEO4J_BOLT_PORT`,
`MINIO_API_PORT`, `MINIO_CONSOLE_PORT`.

Default admin (from `.env` / seed on startup):

- Username: value of `ADMIN_USERNAME` (default `admin`)
- Password: value of `ADMIN_PASSWORD` (default `admin`)

Keep `ENVIRONMENT=local` for demo secrets. Staging/production reject weak defaults
(admin/postgres/minioadmin/`local-dev-only…` JWT, etc.).

Docker assets for this API live under [`docker/`](docker/README.md). Run Compose from the repository root.

---

## Local development

Run Postgres, Neo4j, and Redis yourself (or start them via the full Compose stack and stop the app services), then run the API and workers on the host.

### 1. Dependencies

Local development uses **Poetry** (hooks expect it). Requires Poetry 2+ and Python 3.11+.

```bash
poetry install --with dev
```

`requirements.txt` is the **runtime** lock export used by Docker production/`runtime` image stages.  
`requirements-dev.txt` is the **dev/test** group (pytest, ruff, mypy, …) used by the Compose/`ci` image and the CI quality job.

Poetry 2 does not bundle `export` by default; this repo declares `poetry-plugin-export` under
`[tool.poetry.requires-plugins]` (installed automatically on `poetry install`).

After changing deps with Poetry, re-export and verify:

```bash
poetry export -f requirements.txt --without-hashes -o requirements.txt
poetry export -f requirements.txt --without-hashes --only dev -o requirements-dev.txt
python scripts/check_requirements_sync.py
```

CI runs the same sync check on every push / PR.
### 2. Pre-commit & Commitizen

```bash
poetry run pre-commit install
poetry run pre-commit install --hook-type pre-push
poetry run pre-commit install --hook-type commit-msg
```

Hook split (so commits stay fast):

| When | What runs |
|------|-----------|
| **commit** | Fast checks: Ruff, pyupgrade, detect-secrets, basic file hygiene |
| **commit-msg** | Commitizen message format (`poetry run cz commit` recommended) |
| **push** | Heavy checks: mypy, Bandit, full pytest |

CI still runs the quality suite on PRs / pushes regardless of local hooks.

### 3. Environment

```bash
cp .env.example .env
```

For a **host** process (not inside Compose), point services at localhost, for example:

```env
POSTGRES_HOST=127.0.0.1
POSTGRES_HOST_TEST=127.0.0.1
POSTGRES_DB_TEST=family_tree_test
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1
NEO4J_URI=bolt://127.0.0.1:7687
JWT_SECRET=local-dev-only-change-me-32chars-min
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:8001
```

`.env.example` uses Docker DNS names (`db`, `redis`, `neo4j`) suitable for Compose. Always set `POSTGRES_DB_TEST` to a **separate** database (e.g. `family_tree_test`); do not point tests at the app DB.

### 4. Migrations

```bash
poetry run alembic upgrade head
```

Schema history is a single initial revision (`0001_initial`). If you previously applied older multi-step revisions, reset the database (drop volume / recreate schema) before upgrading.

### 5. API

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 6. Celery worker and beat

Workers must listen on the routed queues. On Windows (and for simple local runs), use `--pool=solo`:

```bash
poetry run celery -A app.celery.celery_app worker -l info --pool=solo \
  -Q celery,sync_person,sync_relationship,backup_database

poetry run celery -A app.celery.celery_app beat --loglevel=info
```

Optional Flower:

```bash
poetry run celery -A app.celery.celery_app flower --port=5555
```

Without a running worker, Postgres writes still succeed, but Neo4j will not stay in sync.

---

## Configuration

Managed via environment variables / `.env` (`app/core/config.py`). See `.env.example` for a complete template.

| Variable | Purpose |
|----------|---------|
| `POSTGRES_*` | Application database (`HOST`, `USER`, `PASSWORD`, `DB`, `PORT`) |
| `POSTGRES_*_TEST` | Test database (keep `POSTGRES_DB_TEST` distinct from `POSTGRES_DB`) |
| `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` | Graph database |
| `JWT_SECRET` | **Required**, minimum **32** characters |
| `JWT_ALGORITHM` | Default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime (default `15`) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime (default `7`) |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_ROLE_NAME` | Bootstrapped admin |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Celery / Redis |
| `BACKUP_DIR` | Backup output directory (Compose default `/mnt/backups`) |
| `CORS_ORIGINS` | Comma-separated allowed origins (include Vite `http://localhost:5173` for the frontend) |
| `FLOWER_BASIC_AUTH` | Flower `user:password` (default `admin:admin`) |
| `AUTH_RATE_LIMIT_PER_MINUTE` | Auth endpoint rate limit (default `30`) |
| `API_PORT`, `FLOWER_PORT`, `POSTGRES_PUBLISH_PORT`, `REDIS_PUBLISH_PORT`, `NEO4J_HTTP_PORT`, `NEO4J_BOLT_PORT` | Optional published ports for Compose |

---

## API overview

### REST

Interactive docs: [/api_docs](http://localhost:8001/api_docs) (default `/docs` is disabled; local Swagger assets).

| Prefix | Resources |
|--------|-----------|
| `/auth` | `POST /login`, `POST /refresh`, `POST /logout`, `POST /logout-all`, `GET /me` |
| `/users` | User CRUD (permission-guarded) |
| `/roles` | Role CRUD |
| `/permissions` | Permission listing |
| `/persons` | Person CRUD, filtered list, closest relationship |
| `/marriages` | Marriage CRUD, divorce, filtered list |
| `/health` | Postgres + Neo4j status (`200` / `status:ok`, or `503` / `status:degraded`) |
| `/health/neo4j` | Neo4j probe |

Closest relationship:

```http
GET /persons/{from_person_id}/relation/{to_person_id}
Authorization: Bearer <access_token>
```

Returns path distance, node IDs, and relationship types when a path exists in Neo4j (requires prior sync).

Person `birthDate` / `birth_date` values use **Jalali** `YYYY/MM/DD` strings (aligned with the frontend).

### GraphQL API

Endpoint: [`POST /graphql`](http://localhost:8001/graphql) (GraphiQL UI in browser).

GraphQL mirrors REST: same use cases, JWT auth (`Authorization: Bearer <access_token>`), and permission codes.

| GraphQL | REST equivalent |
|---------|-----------------|
| `login` / `refreshToken` / `logout` / `logoutAll` / `me` | `/auth/*` |
| `person` / `persons` / `createPerson` / `updatePerson` / `deletePerson` / `closestRelationship` | `/persons/*` |
| `user` / `users` / `createUser` / `updateUser` / `deleteUser` | `/users/*` |
| `role` / `roles` / `createRole` / `updateRole` / `deleteRole` | `/roles/*` |
| `permissions` | `/permissions/list` |
| `marriage` / `marriages` / `createMarriage` / `updateMarriage` / `deleteMarriage` / `divorce` | `/marriages/*` |

Example login + create person:

```graphql
mutation {
  login(username: "admin", password: "admin") {
    accessToken
    refreshToken
  }
}

mutation {
  createPerson(data: { name: "Ali", gender: MALE, birthDate: "1375/05/10" }) {
    id
    name
    gender
    birthDate
  }
}
```

Send the access token as `Authorization: Bearer …` on subsequent GraphQL requests (same as REST).

Domain errors surface as GraphQL `errors[]` with `extensions.error_code`, `extensions.status`, and localized `message` (aligned with REST error payloads).

---

## Authentication & authorization

1. `POST /auth/login` with OAuth2 form fields `username` and `password` (or GraphQL `login`)
2. Use `access_token` as `Authorization: Bearer …` on protected REST routes and GraphQL operations
3. `POST /auth/refresh` with JSON `{ "refresh_token": "…" }` (or GraphQL `refreshToken`) to rotate tokens
4. `POST /auth/logout` / GraphQL `logout` revokes the current session; `logout-all` / `logoutAll` revokes every session for the user
5. Refresh tokens are **not** accepted as API access tokens

### Session security

Refresh tokens are tracked in `user_sessions`:

- Only a **SHA-256 hash** of the refresh token is stored (never the raw token)
- Each refresh **rotates** the session (old refresh becomes invalid)
- Reuse of a rotated refresh token **revokes all sessions** for that user (theft detection)
- Access tokens carry `sid` (session id); revoked sessions cannot call protected APIs
- Optional metadata: `user_agent`, `ip_address`

Permissions are attached to roles (e.g. `person_create`, `marriage_divorce`). REST uses `RequirePermission(...)`; GraphQL uses the same permission strings via resolver guards.

On startup the app seeds permissions and ensures the configured admin user/role exist.

---

## Background jobs

| Job | Trigger | Behavior |
|-----|---------|----------|
| `sync.person.*` | After person create/update/delete | Upsert/delete Neo4j person; parent edges |
| `sync.relationship.*` | After marriage create/update/divorce/delete | Spouse edges |
| `backup.database` | Celery Beat daily at 00:00 (`Asia/Tehran`) | Postgres dump (+ Neo4j backup helpers) |

Task routing uses dedicated queues; the worker command above must include them.

---

## Testing & quality

```bash
# Full suite
poetry run pytest .

# With coverage (CI uses --cov-fail-under=55)
poetry run pytest -v --cov=app --cov-report=term-missing

# Lint / types / security (as in CI)
poetry run ruff check .
poetry run mypy .
poetry run bandit -r app -ll
```

Test layout:

- `tests/unit` — entities, use cases, mappers, services
- `tests/integration` — SQL repositories; Neo4j repository (skips if Neo4j is unreachable)
- `tests/e2e` — HTTP API via ASGI (graph sync stubbed so Redis is not required)
  - `tests/e2e/routers` — REST
  - `tests/e2e/graphql` — GraphQL (`POST /graphql`)

Docker-based CI creates `POSTGRES_DB_TEST` inside the Compose Postgres service, then runs pytest in the `api` container with coverage gate `50`.

See [Pre-commit & Commitizen](#2-pre-commit--commitizen) for which checks run on commit vs push.

---

## CI / GitHub Actions

Workflow: [`ci.yml`](.github/workflows/ci.yml) on push / PR to `main`.

| Job | What it does |
|-----|--------------|
| **quality** | Ruff, mypy, Bandit on the runner |
| **stack** | Build `docker/compose.yml`, start `api` (+ Postgres / Redis / Neo4j / MinIO), create test DB, run pytest with coverage (≥55%) |

Infra versions match Compose (`postgres:15.13`, `redis:8.2.1`, `neo4j:5.26.4`, pinned MinIO release tags).

Simulate locally:

```bash
cp .env.example .env
docker compose -f docker/compose.yml --env-file .env up --build -d
docker compose -f docker/compose.yml --env-file .env exec -T db \
  psql -U postgres -c "CREATE DATABASE family_tree_test;" || true
docker compose -f docker/compose.yml --env-file .env exec -T api pytest -v --cov=app --cov-fail-under=55
```

---

## Project layout

```
app/
  application/     # Use cases, DTOs, application services
  domain/          # Entities, exceptions, repository interfaces
  infrastructure/  # DB models, SQL/Neo4j repos, security, UoW
  presentation/
    rest/          # FastAPI routers, schemas, dependencies
    graphql/       # Strawberry schema, types, resolvers (synced with REST)
  celery/          # Celery app and tasks
  core/            # Settings
docker/            # Dockerfile, entrypoint, compose.yml
.github/workflows/ # GitHub Actions (ci.yml)
bruno/             # Bruno API collection
migrations/        # Alembic revisions
tests/             # unit / integration / e2e (REST + GraphQL)
```

---

## API client (Bruno)

Open the `bruno/` collection in [Bruno](https://www.usebruno.com/). Use the `Local` environment (`base_url`, credentials, tokens). Requests cover auth, users, roles, permissions, persons (including closest relationship), marriages, and GraphQL counterparts under `bruno/GraphQL/`.

---

## Seeding sample data

Permissions and the admin user are seeded automatically on API startup.

Optional family sample data:

1. Copy `seed_items.sample.py` to `seed_items.py` (the latter is gitignored).
2. Fill the person and marriage lists in `seed_items.py`.
3. Import and uncomment in `app/main.py` lifespan:
   ```python
   from seed_items import seed_initial_items
   # ...
   await seed_initial_items(uow=uow)
   ```
4. Restart the API.

---

## Known limitations

- Neo4j graph edges are written by Celery sync; without workers the graph stays empty aside from tests that seed Neo4j directly.
- Example `.env` credentials are for `ENVIRONMENT=local` only; staging/production refuse weak defaults.

---

## Roadmap

- [ ] Redis caching for hot graph paths
- [ ] Observability (structured metrics / OpenTelemetry)
- [x] Live Neo4j closest-relationship e2e in CI
- [x] GraphQL API synced with REST

---

## License

Released under the [MIT License](LICENSE).

---

Developed by **Arash Alfooneh**.
