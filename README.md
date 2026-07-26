# Family Tree API

Production-oriented backend for managing family trees: people, marriages, and graph relationships.

Built with **FastAPI** and **Clean Architecture**. **PostgreSQL** is the source of truth for transactional data; **Neo4j** stores parent/spouse edges for traversals such as shortest-path (closest relationship) queries. Background work runs on **Celery** + **Redis**.

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
- Closest relationship between two people: `GET /persons/{from_id}/relation/{to_id}`
- JWT auth with access + refresh tokens
- Role-based access control (permissions on roles)
- Async SQLAlchemy + Alembic migrations
- Celery sync of person/marriage changes into Neo4j after commit
- Scheduled database backups via Celery Beat
- Docker Compose stack (API, worker, beat, Flower, Postgres, Redis, Neo4j)
- Bruno collection for manual API testing
- CI: Ruff, mypy, Bandit, Pytest (GitHub Actions)

---

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  FastAPI    │────▶│  Use cases /     │────▶│ PostgreSQL  │
│  (HTTP)     │     │  domain services │     │ (source of  │
└─────────────┘     └────────┬─────────┘     │  truth)     │
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
| **Presentation** | Routers, Pydantic schemas, auth/permission guards, mappers |
| **Application** | Use cases, DTOs, authorization & graph-sync services |
| **Domain** | Entities, invariants, repository ports, marriage rules |
| **Infrastructure** | SQLAlchemy, Neo4j client, JWT/Argon2, Unit of Work, Celery |
| **Celery** | Person/relationship sync tasks, scheduled backups |

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
| API | FastAPI, Uvicorn |
| ORM / DB | SQLAlchemy 2 (async), asyncpg, Alembic, PostgreSQL 15 |
| Graph | Neo4j 5 |
| Queue | Celery, Redis 8, Flower |
| Auth | OAuth2 password flow, JWT (`python-jose`), Argon2 (`passlib`) |
| Validation | Pydantic v2 |
| Quality | Ruff, mypy, Bandit, pre-commit, Commitizen, Pytest |

---

## Quick start (Docker)

**Requirements:** Docker and Docker Compose.

```bash
cp .env.example .env
# Edit .env if needed. JWT_SECRET must be at least 32 characters.

docker compose up --build
```

The API entrypoint waits for Postgres, runs `alembic upgrade head`, then starts Uvicorn.

| Service | URL |
|---------|-----|
| API | http://localhost:8001 |
| Swagger UI | http://localhost:8001/api_docs |
| ReDoc | http://localhost:8001/redoc |
| OpenAPI JSON | http://localhost:8001/openapi.json |
| Health | http://localhost:8001/health |
| Neo4j Browser | http://localhost:7474 |
| Flower | http://localhost:5555 |

Default admin (from `.env` / seed on startup):

- Username: value of `ADMIN_USERNAME` (default `admin`)
- Password: value of `ADMIN_PASSWORD` (default `admin`)

Change these before any shared or production-like environment.

---

## Local development

Run Postgres, Neo4j, and Redis yourself (or start only those services via Compose), then run the API and workers on the host.

### 1. Dependencies

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix:    source .venv/bin/activate

pip install -r requirements.txt
# or: poetry install
```

### 2. Environment

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

### 3. Migrations

```bash
alembic upgrade head
```

> **Warning:** revision `a1b2c3d4e5f6` (integer IDs → UUID) is **destructive**. It drops and recreates application tables. Do not run it against a database that holds data you need to keep.

### 4. API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
# or: poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 5. Celery worker and beat

Workers must listen on the routed queues:

```bash
celery -A app.celery.celery_app worker -l info --pool=solo \
  -Q celery,sync_person,sync_relationship,backup_database

celery -A app.celery.celery_app beat --loglevel=info
```

Optional Flower:

```bash
celery -A app.celery.celery_app flower --port=5555
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

Interactive docs: [/api_docs](http://localhost:8001/api_docs).

| Prefix | Resources |
|--------|-----------|
| `/auth` | `POST /login`, `POST /refresh`, `GET /me` |
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

---

## Authentication & authorization

1. `POST /auth/login` with OAuth2 form fields `username` and `password`
2. Use `access_token` as `Authorization: Bearer …` on protected routes
3. `POST /auth/refresh` with JSON `{ "refresh_token": "…" }` to rotate tokens
4. `POST /auth/logout` revokes the current session; `POST /auth/logout-all` revokes every session for the user
5. Refresh tokens are **not** accepted as API access tokens

### Session security

Refresh tokens are tracked in `user_sessions`:

- Only a **SHA-256 hash** of the refresh token is stored (never the raw token)
- Each refresh **rotates** the session (old refresh becomes invalid)
- Reuse of a rotated refresh token **revokes all sessions** for that user (theft detection)
- Access tokens carry `sid` (session id); revoked sessions cannot call protected APIs
- Optional metadata: `user_agent`, `ip_address`

Permissions are attached to roles (e.g. `person_create`, `marriage_divorce`). Endpoint guards use `RequirePermission(...)`.

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
pytest .

# With coverage (CI uses --cov-fail-under=50)
pytest -v --cov=app --cov-report=term-missing

# Lint / types / security (as in CI)
ruff check .
mypy .
bandit -r app -ll
```

Test layout:

- `tests/unit` — entities, use cases, mappers, services
- `tests/integration` — SQL repositories; Neo4j repository (skips if Neo4j is unreachable)
- `tests/e2e` — HTTP API via ASGI (graph sync stubbed so Redis is not required)

Pre-commit hooks and Commitizen are configured for local quality gates (`pre-commit install`).

---

## Project layout

```
app/
  application/     # Use cases, DTOs, application services
  domain/          # Entities, exceptions, repository interfaces
  infrastructure/  # DB models, SQL/Neo4j repos, security, UoW
  presentation/    # FastAPI routers, schemas, dependencies
  celery/          # Celery app and tasks
  core/            # Settings
bruno/             # Bruno API collection
migrations/        # Alembic revisions
tests/             # unit / integration / e2e
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

---

## License

Intended for educational and development purposes.

---

Developed by **Arash Alfooneh**.
