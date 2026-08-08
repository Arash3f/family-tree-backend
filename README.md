# Family Tree API

Production-oriented backend for managing family trees: people, marriages, and graph relationships.

Built with **FastAPI** and **Clean Architecture**. Exposes both **REST** and **GraphQL** APIs over the same use cases. **PostgreSQL** is the source of truth for transactional data; **Neo4j** stores parent/spouse edges for traversals such as shortest-path (closest relationship) queries. Background work runs on **Celery** + **Redis**.

| | |
|---|---|
| **Version** | `0.1.0` |
| **Python** | `3.11+` |
| **License** | Educational / development use |

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
- Docker stack under `docker/` (full or app-only Compose; multi-stage image)
- Bruno collection for manual REST API testing
- CI: Ruff, mypy, Bandit, Pytest (GitHub Actions)

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
| ORM / DB | SQLAlchemy 2 (async), asyncpg, Alembic, PostgreSQL 15 |
| Graph | Neo4j 5 |
| Queue | Celery, Redis 8, Flower |
| Auth | OAuth2 password flow, JWT (`python-jose`), Argon2 (`passlib`) |
| Validation | Pydantic v2 |
| Quality | Ruff, mypy, Bandit, pre-commit, Commitizen, Pytest |

---

## Quick start (Docker)

**Requirements:** Docker and Docker Compose.

All Docker assets live under [`docker/`](docker/README.md).

```bash
cp .env.example .env
# Edit .env if needed. JWT_SECRET must be at least 32 characters.
```

### Full stack (all services)

Starts API, Celery worker/beat, Flower, Postgres, Redis, and Neo4j.

```bash
docker compose -f docker/compose.full.yml --env-file .env up --build
```

`.env.example` already uses Docker DNS names (`db`, `redis`, `neo4j`) for this mode.

### App only

Starts only the project containers (API, Celery worker/beat, Flower).

**A) Infra on the host** (Postgres/Redis/Neo4j installed locally):

```bash
docker compose -f docker/compose.app.yml --env-file .env up --build
```

Defaults use `host.docker.internal`. Override with `APP_POSTGRES_HOST`, `APP_CELERY_BROKER_URL`, `APP_CELERY_RESULT_BACKEND`, `APP_NEO4J_URI` if needed.

**B) Infra from full Compose** (only `db` / `redis` / `neo4j` already up):

```bash
docker compose -f docker/compose.full.yml --env-file .env up -d db redis neo4j
docker compose -f docker/compose.app.yml -f docker/compose.app.with-infra.yml --env-file .env up --build
```

With Docker DNS overrides:

```bash
# PowerShell
$env:APP_POSTGRES_HOST="db"
$env:APP_CELERY_BROKER_URL="redis://redis:6379/0"
$env:APP_CELERY_RESULT_BACKEND="redis://redis:6379/1"
$env:APP_NEO4J_URI="bolt://neo4j:7687"
```

The API entrypoint waits for Postgres, runs `alembic upgrade head`, then starts Uvicorn.

| Service | URL |
|---------|-----|
| API | http://localhost:8001 |
| Swagger UI | http://localhost:8001/api_docs |
| ReDoc | http://localhost:8001/redoc |
| OpenAPI JSON | http://localhost:8001/openapi.json |
| GraphQL (GraphiQL) | http://localhost:8001/graphql |
| Health | http://localhost:8001/health |
| Neo4j Browser | http://localhost:7474 |
| Flower | http://localhost:5555 |

Default admin (from `.env` / seed on startup):

- Username: value of `ADMIN_USERNAME` (default `admin`)
- Password: value of `ADMIN_PASSWORD` (default `admin`)

Change these before any shared or production-like environment.

---

## Local development

Run Postgres, Neo4j, and Redis yourself (or start them via the full Compose stack and stop the app services), then run the API and workers on the host.

### 1. Dependencies

Local development uses **Poetry** (hooks expect it). Requires Poetry 2+ and Python 3.11+.

```bash
poetry install
```

`requirements.txt` is the lock export used by **Docker** and **CI**. After changing deps with Poetry, re-export:

```bash
poetry export -f requirements.txt --without-hashes -o requirements.txt
```

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

CI still runs the full quality suite on every PR regardless of local hooks.

### 3. Environment

```bash
cp .env.example .env
```

For a **host** process (not inside Compose), point services at localhost, for example:

```env
POSTGRES_HOST=127.0.0.1
POSTGRES_HOST_TEST=127.0.0.1
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1
NEO4J_URI=bolt://127.0.0.1:7687
JWT_SECRET=local-dev-only-change-me-32chars-min
```

`.env.example` uses Docker DNS names (`db`, `redis`, `neo4j`) suitable for Compose.

### 4. Migrations

```bash
poetry run alembic upgrade head
```

> **Warning:** revision `a1b2c3d4e5f6` (integer IDs → UUID) is **destructive**. It drops and recreates application tables. Do not run it against a database that holds data you need to keep.

### 5. API

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 6. Celery worker and beat

Workers must listen on the routed queues:

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

Managed via environment variables / `.env` (`app/core/config.py`).

| Variable | Purpose |
|----------|---------|
| `POSTGRES_*` | Application database |
| `POSTGRES_*_TEST` | Test database |
| `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` | Graph database |
| `JWT_SECRET` | **Required**, minimum **32** characters |
| `JWT_ALGORITHM` | Default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_ROLE_NAME` | Bootstrapped admin |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Celery / Redis |
| `BACKUP_DIR` | Backup output directory |

---

## API overview

### REST

Interactive docs: [/api_docs](http://localhost:8001/api_docs).

| Prefix | Resources |
|--------|-----------|
| `/auth` | `POST /login`, `POST /refresh`, `POST /logout`, `POST /logout-all`, `GET /me` |
| `/users` | User CRUD (permission-guarded) |
| `/roles` | Role CRUD |
| `/permissions` | Permission listing |
| `/persons` | Person CRUD, filtered list, closest relationship |
| `/marriages` | Marriage CRUD, divorce, filtered list |
| `/health` | Postgres + Neo4j status |
| `/health/neo4j` | Neo4j probe |

Closest relationship:

```http
GET /persons/{from_person_id}/relation/{to_person_id}
Authorization: Bearer <access_token>
```

Returns path distance, node IDs, and relationship types when a path exists in Neo4j (requires prior sync).

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

# With coverage (CI uses --cov-fail-under=50)
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

See [Pre-commit & Commitizen](#2-pre-commit--commitizen) for which checks run on commit vs push.

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
docker/            # Dockerfile, entrypoint, Compose stacks
bruno/             # Bruno API collection
migrations/        # Alembic revisions
tests/             # unit / integration / e2e (REST + GraphQL)
```

---

## API client (Bruno)

Open the `bruno/` collection in [Bruno](https://www.usebruno.com/). Use the `Local` environment (`base_url`, credentials, tokens). Requests cover auth, users, roles, permissions, persons (including closest relationship), and marriages.

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

- Neo4j stays empty unless Celery workers are running and reachable.
- Migration `a1b2c3d4e5f6` wipes existing relational data (UUID cutover).
- Default admin password and JWT secret in examples are for local use only.

---

## Roadmap

- [ ] Redis caching for hot graph paths
- [ ] Observability (structured metrics / OpenTelemetry)
- [ ] Non-destructive migration path for UUID upgrades with existing data
- [ ] Broader e2e coverage with live Neo4j assertions
- [x] GraphQL API synced with REST

---

## License

Intended for educational and development purposes.

---

Developed by **Arash Alfooneh**.
