# Family Tree Backend

> Multi-tenant genealogy API. Records people, parentage and marriages in PostgreSQL, mirrors the
> kinship graph into Neo4j, and answers "how are these two related?" over the graph.

**FastAPI · PostgreSQL · Neo4j · Celery · Redis · MinIO — REST and GraphQL over one set of use cases.**

| | |
|---|---|
| Version | `0.1.0` |
| Python | `3.11+` |
| Tests | 631 passing, 88% coverage |
| License | [MIT](LICENSE) |

---

## Contents

- [What it does](#what-it-does)
- [Architecture](#architecture)
- [Quick start](#quick-start)
- [Local development](#local-development)
- [API reference](#api-reference)
- [Configuration](#configuration)
- [Testing and quality](#testing-and-quality)
- [CI](#ci)
- [Project layout](#project-layout)
- [Operations](#operations)
- [Troubleshooting](#troubleshooting)

---

## What it does

A family tree is a tenant. Users are granted access to individual trees, and every query is scoped to
the tree it belongs to — data never crosses tenant boundaries, including inside graph traversals.

Within a tree you can:

- Register **persons** with names, gender, birth/death dates and places, notes and a photo
- Link **parents** to children, tagged `BIOLOGICAL`, `ADOPTIVE` or `STEP`
- Record **marriages** and divorces
- Ask for the **closest relationship path** between any two people, computed in Neo4j
- **Import and export** whole trees as Excel workbooks
- Manage **users, roles and permissions**, and raise **support tickets**

### Design notes

**One behaviour, two protocols.** REST and GraphQL are thin presentation layers over the same use
cases, so authorization, validation and error semantics cannot drift apart. Every field in
[schema.graphql](schema.graphql) documents the REST route it mirrors.

**Postgres is the source of truth.** Writes commit there first. A Celery task then mirrors the change
into Neo4j, which exists purely as a query accelerator for path finding — it can be rebuilt from
Postgres at any time, and an hourly reconciliation task repairs drift.

**Tenancy is enforced in Cypher, not just in Python.** Path queries are scoped by `tree_id`, so a
person who appears in two trees cannot act as a bridge between two otherwise unrelated people.

---

## Architecture

```
                 REST (FastAPI)          GraphQL (Strawberry)
                 Pydantic schemas         typed resolvers
                        └────────────┬────────────┘
                                     │  same guards, same errors
                        ┌────────────▼────────────┐
                        │      APPLICATION        │
                        │  use cases · DTOs       │
                        │  authorization · Excel  │
                        └────────────┬────────────┘
                                     │  repository interfaces
                        ┌────────────▼────────────┐
                        │         DOMAIN          │
                        │  entities · rules       │
                        └────────────┬────────────┘
                                     │
            ┌────────────────────────┼────────────────────────┐
            │            INFRASTRUCTURE / WORKERS             │
            │  SQLAlchemy · UoW · JWT/Argon2 · Neo4j · MinIO  │
            └───┬────────────┬───────────┬──────────────┬─────┘
                │            │           │              │
           ┌────▼────┐  ┌────▼────┐ ┌────▼────┐   ┌─────▼─────┐
           │Postgres │  │  Neo4j  │ │  Redis  │   │   MinIO   │
           │   15    │  │  5.26   │ │    8    │   │  photos   │
           │ truth   │  │  graph  │ │ broker  │   │           │
           └─────────┘  └─────────┘ └─────────┘   └───────────┘
```

Dependencies point inward. Domain and application layers know only interfaces; concrete drivers live
in `infrastructure` and are injected at the edge.

### Write path

1. Request authenticated (JWT) and authorized against the caller's permissions **for that tree**
2. Use case applies domain rules and commits through the Unit of Work — Postgres now holds the truth
3. A Celery task is queued to mirror the person or relationship into Neo4j
4. Reads that need traversal hit Neo4j; everything else reads Postgres directly

Neo4j is eventually consistent, typically within a second. If a sync task exhausts its retries it is
logged at `CRITICAL`, and the hourly `reconcile.neo4j` task repairs the difference.

### Storage responsibilities

| Store | Owns |
|-------|------|
| **PostgreSQL** | Users, roles, permissions, trees, memberships, persons, marriages, tickets |
| **Neo4j** | `Person` nodes and parent/spouse edges — a derived, rebuildable projection |
| **Redis** | Celery broker (db 0) and results (db 1); auth rate-limit windows (db 2) |
| **MinIO** | Person photos in a private bucket, served as presigned URLs |

---

## Tech stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Framework | FastAPI 0.136 | Async, OpenAPI out of the box, first-class Strawberry integration |
| GraphQL | Strawberry 0.323 | Schema from typed Python, shares dependencies with REST |
| Database | PostgreSQL 15 | Transactional integrity for the system of record |
| Graph | Neo4j 5.26 | Cypher `shortestPath` beats recursive CTEs for kinship queries |
| ORM | SQLAlchemy 2 (asyncpg) | Async sessions, explicit Unit of Work |
| Validation | Pydantic v2 | Request/response models and settings validation |
| Tasks | Celery 5.6 + Redis 8 | Queue routing, scheduled beat jobs, retries |
| Objects | MinIO via aioboto3 | S3-compatible, swap for real S3 without code changes |
| Auth | JWT + Argon2 | Rotating refresh tokens, revocable sessions |
| Quality | Ruff · mypy · Bandit | Lint, strict-ish typing, security scan — all gate CI |

---

## Quick start

**Requires Docker with Compose v2.** Run every command from the repository root.

```bash
cp .env.example .env
docker compose -f docker/compose.yml --env-file .env up --build
```

The API waits for Postgres, runs `alembic upgrade head`, seeds permissions and the admin user, then
serves on **http://localhost:8001**.

| | |
|---|---|
| Swagger UI | http://localhost:8001/api_docs |
| ReDoc | http://localhost:8001/redoc |
| GraphiQL | http://localhost:8001/graphql |
| Health | http://localhost:8001/health |

Only the API port is published. Postgres, Redis, Neo4j and MinIO stay on the internal network unless
you add the host-ports overlay:

```bash
docker compose -f docker/compose.yml -f docker/compose.host-ports.yml --env-file .env up -d
```

### First requests

Log in (OAuth2 password form, default credentials `admin` / `admin`):

```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"
```

```json
{ "access_token": "eyJhbGciOi...", "refresh_token": "eyJhbGciOi...", "token_type": "bearer" }
```

Create a tree, then add a person to it:

```bash
TOKEN=<access_token>

curl -X POST http://localhost:8001/family-trees \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Karimi Family"}'

curl -X POST http://localhost:8001/family-trees/$TREE_ID/persons \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Ali", "gender": "MALE", "birthDate": "1975-04-12"}'
```

Ask how two people are related — this one goes through Neo4j:

```bash
curl "http://localhost:8001/family-trees/$TREE_ID/persons/$FROM_ID/relation/$TO_ID" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{ "fromPersonId": "...", "toPersonId": "...", "found": true, "distance": 3,
  "pathPersonIds": ["...", "...", "..."], "relationshipTypes": ["PARENT_OF", "PARENT_OF"] }
```

> Access tokens live 5 minutes by default. Use `POST /auth/refresh` to rotate rather than
> logging in again.

---

## Local development

Running the app on the host while the datastores stay in Docker is usually the fastest loop.

### 1. Install

Requires **Poetry 2+**:

```bash
poetry install --with dev
poetry run pre-commit install
poetry run pre-commit install --hook-type pre-push
poetry run pre-commit install --hook-type commit-msg
```

| Hook stage | Runs | Roughly |
|------------|------|---------|
| `commit` | Ruff, pyupgrade, detect-secrets, YAML/TOML checks, `.env`/requirements sync | ~1s |
| `commit-msg` | Commitizen format — use `poetry run cz commit` | instant |
| `pre-push` | mypy, Bandit | ~20s |

The test suite is **not** in the pre-push hook (it needs live databases); CI is what enforces it.

### 2. Point the app at localhost

`.env.example` uses Docker DNS names (`db`, `redis`, `neo4j`, `minio`). For host-based development,
override the hosts and publish the datastore ports:

```env
POSTGRES_HOST=127.0.0.1
POSTGRES_HOST_TEST=127.0.0.1
NEO4J_URI=bolt://127.0.0.1:7687
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1
MINIO_ENDPOINT=127.0.0.1:9000
```

```bash
docker compose -f docker/compose.yml -f docker/compose.host-ports.yml --env-file .env up -d db redis neo4j minio
poetry run alembic upgrade head
```

### 3. Run the processes

```bash
# API, with reload
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Worker — must consume every routed queue
poetry run celery -A app.celery.celery_app worker -l info --pool=solo \
  -Q celery,sync_person,sync_relationship,backup_database,reconcile_neo4j

# Scheduler (nightly backup, hourly reconciliation)
poetry run celery -A app.celery.celery_app beat --loglevel=info
```

Without a worker, Postgres writes still succeed but Neo4j never updates, so relationship queries
return `found: false`.

### 4. Migrations

Migrations are a linear chain in `migrations/versions/` (currently through `0019_soft_delete_mtt`).

```bash
poetry run alembic revision --autogenerate -m "describe change"
poetry run alembic upgrade head
```

`tests/integration/migrations/` asserts the migrated schema matches the SQLAlchemy models, so a
hand-edited migration that drifts from the ORM fails CI.

### 5. Regenerating contracts

The OpenAPI document, GraphQL schema and both generated clients are committed and checked for drift:

```bash
poetry run python scripts/export_openapi_schema.py
poetry run python scripts/export_graphql_schema.py
poetry run ariadne-codegen client

poetry run python scripts/check_openapi_client_sync.py
poetry run python scripts/check_graphql_client_sync.py
```

---

## API reference

Base path is `/` — there is no `/api` prefix. All routes except `/auth/login`, `/health` and
`/health/neo4j` require `Authorization: Bearer <access_token>`.

List endpoints are **`POST .../list`**, not `GET`. They take pagination, filters and sorting in the
body, which keeps complex filters expressible without unwieldy query strings:

```jsonc
{ "pagination": { "page": 1, "pageSize": 30 },
  "filters":    { "gender": "FEMALE", "birthDate": { "min": "1950-01-01" } },
  "sortBy": "NAME", "sortOrder": "ASC" }
```

**Dates are ISO `YYYY-MM-DD`.** Jalali `YYYY/MM/DD` is accepted and produced only in Excel
import/export, where the spreadsheets are read by Persian-speaking users.

### Auth and sessions

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/auth/login` | OAuth2 password form → access + refresh tokens |
| `POST` | `/auth/refresh` | Rotate the refresh token |
| `POST` | `/auth/logout` | Revoke the current session |
| `POST` | `/auth/logout-all` | Revoke every session for the user |
| `GET` | `/auth/me` | Current user with roles and permissions |
| `PUT` | `/auth/password` | Change own password |
| `GET` | `/auth/sessions` | List own active sessions |
| `DELETE` | `/auth/sessions/{session_id}` | Revoke one of your sessions |

### Family trees and membership

| Method | Path | Purpose |
|--------|------|---------|
| `GET` `POST` | `/family-trees` | List trees you can see · create one (you become owner) |
| `GET` `PATCH` `DELETE` | `/family-trees/{tree_id}` | Read · rename · delete |
| `GET` `POST` | `/family-trees/{tree_id}/members` | List members · grant a user access |
| `PATCH` `DELETE` | `/family-trees/{tree_id}/members/{user_id}` | Change that member's access · remove them |

### Persons

| Method | Path | Purpose |
|--------|------|---------|
| `POST` `PUT` | `/family-trees/{tree_id}/persons` | Create · update |
| `POST` | `/family-trees/{tree_id}/persons/list` | Filtered, paginated list |
| `GET` `DELETE` | `/family-trees/{tree_id}/persons/{person_id}` | Read · delete |
| `GET` | `/family-trees/{tree_id}/persons/{from_person_id}/relation/{to_person_id}` | Closest relationship path |

### Marriages

| Method | Path | Purpose |
|--------|------|---------|
| `POST` `PUT` `DELETE` | `/family-trees/{tree_id}/marriages` | Create · update · delete |
| `POST` | `/family-trees/{tree_id}/marriages/list` | Filtered, paginated list |
| `GET` | `/family-trees/{tree_id}/marriages/{marriage_id}` | Read |
| `POST` | `/family-trees/{tree_id}/marriages/divorce` | Record a divorce date |

### Media

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/family-trees/{tree_id}/media/upload` | Upload a photo → `photoObjectKey` |

Set the returned `photoObjectKey` on a person. Reads return a time-limited presigned `photoUrl`
(`MINIO_PRESIGN_EXPIRE_SECONDS`, default one hour); the bucket itself stays private.

### Excel

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/family-trees/{tree_id}/excel/sample` | Download a template workbook |
| `POST` | `/family-trees/{tree_id}/excel/import/preview` | Validate and preview without writing |
| `POST` | `/family-trees/{tree_id}/excel/import` | Import |
| `GET` | `/family-trees/{tree_id}/excel/export` | Export the tree |

Always preview first — it reports row-level validation errors while the tree is untouched.

### Administration

| Method | Path | Purpose |
|--------|------|---------|
| `POST` `PUT` | `/users` · `/roles` | Create · update |
| `POST` | `/users/list` · `/roles/list` · `/permissions/list` | Filtered lists |
| `GET` `DELETE` | `/users/{user_id}` · `/roles/{role_id}` | Read · delete |
| `GET` | `/users/{user_id}/sessions` | Inspect another user's sessions |
| `POST` `DELETE` | `/users/{user_id}/sessions/revoke-all` · `/sessions/{session_id}` | Revoke sessions |
| `POST` `GET` | `/tickets` · `/tickets/{ticket_id}` | Raise · read a ticket |
| `POST` `PATCH` | `/tickets/{ticket_id}/messages` · `/status` | Reply · change status |

Permissions are named constants (`user_create`, `tree_update`, …) with bilingual descriptions, and
some imply others — granting `user_create` requires `user_read` and `role_read`.

### Health

| Method | Path | Behaviour |
|--------|------|-----------|
| `GET` | `/health` | `200 {"status":"ok"}` only if Postgres **and** Neo4j answer; otherwise `503 degraded` |
| `GET` | `/health/neo4j` | Neo4j alone; `503` when unreachable |

`/health` backs the container `HEALTHCHECK`, so a degraded dependency marks the container unhealthy.

### GraphQL

One endpoint, `POST /graphql`, with the same auth header and the same permission checks.

```graphql
mutation { login(username: "admin", password: "admin") { accessToken refreshToken } }

query {
  persons(treeId: "...", data: { pagination: { page: 1, pageSize: 20 } }) {
    total
    items { id name gender birthDate photoUrl parents { parentId relationshipType } }
  }
}

query {
  closestRelationship(treeId: "...", fromPersonId: "...", toPersonId: "...") {
    found distance pathPersonIds relationshipTypes
  }
}
```

GraphiQL and introspection are enabled only when `ENVIRONMENT` is `local`, `development`, `dev` or
`test`. In staging and production the endpoint still serves queries, but the schema is not
browsable, and every document is capped by `GRAPHQL_MAX_DEPTH`, `GRAPHQL_MAX_ALIASES` and
`GRAPHQL_MAX_TOKENS` so one query cannot fan out arbitrarily.

---

## Configuration

Everything is environment-driven and validated by `AppSettings` on import — misconfiguration fails at
startup, not on first request. [.env.example](.env.example) documents every field, and a CI check
fails if a setting is added without documenting it.

### Required

```env
JWT_SECRET=at-least-32-characters-long-change-this
ENVIRONMENT=local            # local | development | staging | production

POSTGRES_HOST=db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=family_tree
POSTGRES_DB_TEST=family_tree_test   # must differ from POSTGRES_DB

NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=change-me

CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin         # seeded on first startup
```

### Startup validation

- `JWT_SECRET` shorter than 32 characters is rejected outright
- Weak demo values for `ADMIN_PASSWORD` and `NEO4J_PASSWORD` (`admin`, `postgres`, `password`, …) are
  refused when `ENVIRONMENT` is `staging` or `production`
- The test database must not share host, port and name with the application database — the e2e suite
  drops and recreates its schema, and this guard is what stops it from wiping real data

### Frequently tuned

```env
ACCESS_TOKEN_EXPIRE_MINUTES=5
REFRESH_TOKEN_EXPIRE_MINUTES=60
AUTH_RATE_LIMIT_PER_MINUTE=30
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

DB_POOL_SIZE=10                 # explicit, so exhaustion is a chosen limit
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT_SECONDS=30
DB_POOL_RECYCLE_SECONDS=1800

MINIO_BUCKET=family-tree        # created on startup if absent
MINIO_PUBLIC_ENDPOINT=localhost:9000   # host in presigned URLs, if it differs internally
MINIO_PRESIGN_EXPIRE_SECONDS=3600

APP_IMAGE_TARGET=runtime        # set to `ci` to get an image with pytest and the linters
API_PORT=8001
BACKUP_DIR=/mnt/backups
```

---

## Testing and quality

The suite is **631 tests at 88% statement coverage**, in three layers:

| Layer | Location | Needs | Covers |
|-------|----------|-------|--------|
| Unit | `tests/unit/` | nothing | Entities, use cases, mappers, schemas, GraphQL types |
| Integration | `tests/integration/` | Postgres, Neo4j | Repositories, model/migration parity, services |
| End-to-end | `tests/e2e/` | Postgres, Neo4j, MinIO | REST routers and GraphQL through ASGI, Celery stubbed |

Integration and e2e tests need live datastores, so run them in the container:

```bash
APP_IMAGE_TARGET=ci docker compose -f docker/compose.yml --env-file .env up -d --build

# once per Postgres volume
docker compose -f docker/compose.yml --env-file .env exec -T db \
  psql -U postgres -c "CREATE DATABASE family_tree_test"

docker compose -f docker/compose.yml --env-file .env exec -T api \
  pytest -v --cov=app --cov-report=term-missing
```

Unit tests alone run on the host with no services:

```bash
poetry run pytest tests/unit -v --no-cov
```

Two suites deliberately exercise the real graph rather than a stub:
`tests/e2e/routers/test_closest_relationship_live.py` runs against live Neo4j, and
`tests/e2e/routers/test_cross_tree_isolation.py` asserts that tenancy holds across both APIs.

> **Known limitation.** Two tests in `tests/integration/repositories/test_neo4j_family_tree_repository.py`
> report `SKIPPED [Neo4j not available]` even when Neo4j is healthy. The async driver is a
> process-wide singleton whose connection pool binds to the event loop that first uses it, while
> pytest-asyncio gives each test a fresh loop; later tests hit `Future attached to a different loop`
> and the fixture treats that as an unavailable database. The behaviour is correct in production,
> where one loop lives for the process lifetime. The same guarantees are covered end to end by the
> live and isolation suites above, so this is a harness gap rather than untested behaviour.

### Static analysis

```bash
poetry run ruff check . && poetry run ruff format --check .
poetry run mypy .                                    # 300 source files, clean
poetry run bandit -r app -c pyproject.toml -ll
poetry run python scripts/check_env_example_sync.py
poetry run python scripts/check_requirements_sync.py
```

Ruff runs `E,F,I,UP,SIM,C4`. Two rule sets are switched off on purpose: bugbear's `B008` fires on
FastAPI's `Depends(...)` defaults, and `RUF001` flags this codebase's intentional Persian strings as
ambiguous Unicode.

### Dependencies

Poetry owns the lock file; the `requirements*.txt` files are exported artifacts that the Docker images
install from. After changing dependencies, re-export or CI will fail:

```bash
poetry export -f requirements.txt --without-hashes -o requirements.txt
poetry export -f requirements.txt --without-hashes --only dev -o requirements-dev.txt
```

---

## CI

[.github/workflows/ci.yml](.github/workflows/ci.yml) runs on every push and PR to `main`, in two jobs.

**Quality** — installs dependencies, then runs Ruff, format check, mypy, Bandit, the `.env.example`
and requirements sync checks, and validates both Compose files.

**Stack** — gated on quality passing:

1. Builds the images
2. Asserts the production image imports `app.main` and **does not** ship pytest
3. Starts the stack and waits for every healthcheck
4. Checks that the applied Alembic revision equals head
5. Creates the test database and runs the suite with `--cov-fail-under=80`
6. Runs the live Neo4j relationship test separately
7. Uploads JUnit and coverage XML, dumps container logs on failure, and always tears down with `-v`

The coverage floor is 80 while actual coverage sits at 88, leaving headroom for a refactor to land
without a red build over a rounding difference.

---

## Project layout

```
family-tree-backend/
├── app/
│   ├── domain/              # Entities, repository interfaces, domain rules, permissions
│   ├── application/         # Use cases, DTOs, services (authorization, Excel), interfaces
│   ├── infrastructure/      # SQLAlchemy, Neo4j, MinIO, JWT/Argon2, Unit of Work, mappers
│   ├── presentation/        # rest/ (routers, schemas, deps) · graphql/ (types, resolvers)
│   ├── celery/              # celery_app.py + tasks/ (sync, reconcile, backup)
│   ├── core/                # AppSettings
│   └── main.py              # App factory, lifespan, middleware, router registration
├── tests/                   # unit/ · integration/ · e2e/ · helpers/
├── migrations/versions/     # Alembic chain, 0001 → 0019
├── docker/                  # Dockerfile (runtime + ci), compose.yml, overlays, entrypoint
├── generated/               # Committed OpenAPI and GraphQL clients (drift-checked)
├── bruno/                   # Bruno API collection, one folder per resource
├── scripts/                 # Schema export, drift checks, backup restore
├── openapi.json             # Committed REST contract
└── schema.graphql           # Committed GraphQL contract
```

Layer boundaries are the load-bearing rule: `domain` imports nothing from the outer layers,
`application` depends on domain interfaces, and only `infrastructure` and `presentation` know about
FastAPI, SQLAlchemy or Neo4j. A use case is testable with no I/O because of it.

---

## Operations

### Background tasks

| Task | Queue | Trigger |
|------|-------|---------|
| `sync.person.*` | `sync_person` | On person write |
| `sync.relationship.*` | `sync_relationship` | On parentage or marriage change |
| `reconcile.neo4j` | `reconcile_neo4j` | Beat, hourly at :30 |
| `backup.database` | `backup_database` | Beat, daily at 00:00 Asia/Tehran |

> The worker must consume **every** queue listed above. A queue with no consumer accepts messages
> silently and never runs them — the failure looks like nothing happening rather than an error.

A task that exhausts its retries logs at `CRITICAL` with its arguments, naming the entity that is now
out of sync. Reconciliation picks it up within the hour; the log is what tells you it happened.

### Backups

`backup.database` runs nightly and writes two dumps into `BACKUP_DIR` (the `backup_data` volume): a
`pg_dump` of Postgres and a Neo4j export, stamped with a shared timestamp.

```bash
python scripts/restore_backup.py --timestamp 2026-08-18_02-00-00
python scripts/restore_backup.py --timestamp 2026-08-18_02-00-00 --only postgres
```

The two dumps are taken back to back rather than in one transaction, so a write landing between them
can appear on only one side. Restoring both from the same timestamp gets as close to a consistent
point as this strategy allows — check application-level consistency afterwards, and remember that
Neo4j can always be rebuilt from Postgres by reconciliation if the graph side looks wrong.

### Production notes

- Compose builds the lean `runtime` image by default; `APP_IMAGE_TARGET=ci` adds the test tooling, and
  CI actively asserts that pytest never reaches the production image
- Containers run as non-root uid 1000
- Set `ENVIRONMENT=production` to enforce the weak-secret checks and disable GraphQL introspection
- The entrypoint runs `alembic upgrade head` before serving — with multiple replicas, run migrations
  as a separate step first

---

## Troubleshooting

**Relationship queries return `found: false` for people who are clearly related.**
Neo4j has not been told about them. Check the worker is running and consuming the sync queues:

```bash
docker compose -f docker/compose.yml --env-file .env exec celery_worker \
  celery -A app.celery.celery_app inspect active_queues
```

Then check whether messages are piling up on a queue nobody consumes — a non-zero, non-draining
length means the queue is missing from the worker's `-Q` list:

```bash
docker compose -f docker/compose.yml --env-file .env exec redis \
  redis-cli -n 0 llen sync_person
```

**`/health` returns 503.** The body names the failing dependency:

```bash
curl -i http://localhost:8001/health     # {"postgres":"ok","neo4j":"error","status":"degraded"}
```

**Test database will not drop** — connections are still open:

```bash
docker compose -f docker/compose.yml --env-file .env exec db psql -U postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='family_tree_test'"
```

**`pytest: not found` in the container.** The default image is production-only. Rebuild with
`APP_IMAGE_TARGET=ci`.

**`429` on `/auth/login`.** The per-IP sliding window is doing its job; raise
`AUTH_RATE_LIMIT_PER_MINUTE`, set it to `0` to disable, or wait out the minute.

**`503 Authentication is temporarily unavailable`.** Redis is unreachable, and outside development the
limiter fails closed rather than leaving credential stuffing unmetered. Fix Redis — that is the bug.

**Photo uploads succeed but `photoUrl` is unreachable from the browser.** The presigned URL was signed
with the internal endpoint. Set `MINIO_PUBLIC_ENDPOINT` to the host clients can actually reach.

**Startup fails with a settings error.** Read it literally — `JWT_SECRET` under 32 characters, a weak
password outside local, or a test database pointing at the application database. All three are
deliberate guards.

---

## Contributing

1. Branch from `main` (`feat/`, `fix/`, `ref/`)
2. Commit with `poetry run cz commit` — the `commit-msg` hook enforces the format
3. Update `openapi.json` / `schema.graphql` and the generated clients when the API changes
4. Push; the `pre-push` hook runs mypy and Bandit, and CI runs the full suite

---

## License

MIT — see [LICENSE](LICENSE).

**Maintainer:** Arash Alfooneh · arash.alfooneh@gmail.com
