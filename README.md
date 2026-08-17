# Family Tree Backend

> Production-ready GraphQL & REST API for managing multi-tenant family hierarchies with graph-based relationship queries.

**Built with:** FastAPI • PostgreSQL • Neo4j • Celery • Redis • MinIO

| | |
|---|---|
| **Version** | `0.1.0` |
| **Python** | `3.11+` |
| **License** | MIT |

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Local Development](#local-development)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Testing & Quality](#testing--quality)
- [CI/CD Pipeline](#cicd-pipeline)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)

---

## Overview

### What This Backend Does

A **multi-tenant family tree system** where users can:
- Create and manage family trees
- Add persons with biographical data (names, dates, photos)
- Record marriages and divorces
- Query closest relationships between two people (e.g., "3rd cousin twice removed")
- Bulk import/export data via Excel
- Upload and manage person photos

### Key Features

✅ **Dual API:** REST + GraphQL (same logic, unified behavior)  
✅ **Hybrid Storage:** PostgreSQL (ACID, auth, history) + Neo4j (graph traversals)  
✅ **Multi-Tenancy:** Data never bleeds between family trees  
✅ **Graph Queries:** Shortest-path relationships computed on Neo4j  
✅ **Async Throughout:** SQLAlchemy 2 async, Celery workers, Redis queue  
✅ **Security:** JWT rotation, Argon2 hashing, role-based permissions, rate limiting  
✅ **Background Jobs:** Automated Neo4j sync, scheduled database backups  
✅ **File Storage:** MinIO (S3-compatible) for person photos with presigned URLs  
✅ **High Test Coverage:** 90%+ with unit/integration/e2e suites  
✅ **Production Hardened:** Health checks, structured logging, error tracking  

---

## Architecture

### System Design

```
┌──────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│  ┌─────────────────────┐          ┌──────────────────────┐      │
│  │  REST API (FastAPI) │          │  GraphQL (Strawberry)│      │
│  │  Pydantic schemas   │          │  Type-safe resolvers │      │
│  │  Permission guards  │          │  Same auth/access    │      │
│  └─────────┬───────────┘          └──────────┬───────────┘      │
└────────────┼──────────────────────────────────┼─────────────────┘
             │                                  │
             └──────────────────┬───────────────┘
                                │
┌───────────────────────────────┼─────────────────────────────────┐
│                APPLICATION LAYER                                │
│  Use Cases • DTOs • Authorization • Excel Processing            │
│  (All business logic lives here, reused by REST & GraphQL)      │
└───────────────────────────────┼─────────────────────────────────┘
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
┌────────────▼──────────┐  ┌────▼──────────┐  ┌───▼──────────────┐
│  INFRASTRUCTURE       │  │  DOMAIN       │  │  CELERY WORKERS  │
│  ┌──────────────────┐ │  │  Entities     │  │  ┌────────────────┤
│  │ SQLAlchemy ORM   │ │  │  Repository   │  │  │ Person sync     │
│  │ Unit of Work     │ │  │  Interfaces   │  │  │ Marriage sync    │
│  │ JWT/Argon2       │ │  │  Business     │  │  │ DB backups      │
│  │ Neo4j driver     │ │  │  rules        │  │  └────────────────┤
│  │ MinIO S3         │ │  │               │  │  Redis queue      │
│  └──────────────────┘ │  └───────────────┘  └───────────────────┘
└───────────────────────┘
             │
   ┌─────────┼─────────┬──────────┐
   │         │         │          │
┌──▼──┐  ┌──▼──┐  ┌──▼───┐  ┌───▼───┐
│ PG  │  │ Neo4j  │ Redis │ MinIO │
│ 15  │  │   5    │  8    │       │
└─────┘  └────────┘───────┘───────┘
```

### Data Flow

1. **User Action** → REST/GraphQL endpoint
2. **Authorization** → Check JWT + permissions
3. **Application Logic** → Use cases process request, validate rules
4. **Database Commit** → PostgreSQL is source of truth
5. **Event Published** → Celery task queued to sync Neo4j
6. **Graph Updated** → Neo4j stays eventually consistent with Postgres
7. **Response** → Client receives data with latest changes

### Storage Responsibilities

| Store | Owns |
|-------|------|
| **PostgreSQL** | Users, roles, permissions, persons, marriages, audit history |
| **Neo4j** | Person nodes, PARENT_OF/SPOUSE_OF edges (synced from Postgres) |
| **Redis** | Celery task queue, rate-limit counters, session cache |
| **MinIO** | Person photos with presigned URLs (private bucket) |

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Framework** | FastAPI 0.136+ | Modern, async, OpenAPI docs, Strawberry GraphQL support |
| **API Docs** | Strawberry GraphQL | Type-safe, schema-driven, shares resolvers with auth |
| **Database** | PostgreSQL 15 | ACID, rich query language, async asyncpg driver |
| **Migrations** | Alembic | Git-friendly, reversible schema versioning |
| **Graph DB** | Neo4j 5 | Cypherfor complex path queries, built-in traversal algorithms |
| **ORM** | SQLAlchemy 2 | Async support, declarative schemas, strong typing |
| **Validation** | Pydantic v2 | Runtime validation, serialization, JSON schema |
| **Queue** | Celery 5.6+ | Task routing, scheduled jobs, failure retry |
| **Broker** | Redis 8 | In-memory queue, rate limiting, session storage |
| **Job Monitor** | Flower 2.0+ | Visual task monitoring, retry controls |
| **File Storage** | MinIO + aioboto3 | S3-compatible, presigned URLs, local or cloud |
| **Auth** | JWT + Argon2 | Stateless tokens, password hashing, refresh rotation |
| **Quality** | Ruff + mypy + Bandit | Fast linting, type checking, security scanning |
| **Testing** | pytest + pytest-asyncio | Async fixtures, coverage gates (≥90%), speed |

---

## Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended)
  OR
- **Python 3.11+** + **PostgreSQL 15** + **Redis 8** + **Neo4j 5** (local setup)

### 1. Clone & Setup

```bash
git clone <repo>
cd family-tree-backend
cp .env.example .env

# Edit .env if needed:
# - JWT_SECRET: must be ≥32 characters
# - ADMIN_PASSWORD: change from "admin" for staging/production
```

### 2. Run with Docker (Recommended)

```bash
# Full stack: API + Postgres + Redis + Neo4j + MinIO + Celery + Flower
docker compose -f docker/compose.yml --env-file .env up --build
```

**Endpoints after startup:**

| Service | URL |
|---------|-----|
| **API** | http://localhost:8001 |
| **Swagger UI** | http://localhost:8001/api_docs |
| **ReDoc** | http://localhost:8001/redoc |
| **GraphQL** | http://localhost:8001/graphql |
| **Flower** | http://localhost:5555 (admin:admin) |

### 3. First Request

**Login:**
```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**Create a family tree:**
```bash
curl -X POST http://localhost:8001/family-trees \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Family"}'
```

**Add a person to the tree:**
```bash
curl -X POST http://localhost:8001/family-trees/{tree_id}/persons \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice",
    "gender": "FEMALE",
    "birthDate": "1400/05/10"
  }'
```

---

## Local Development

### 1. Install Dependencies

**Requires Poetry 2+ and Python 3.11+:**

```bash
poetry install --with dev
```

This installs:
- `requirements.txt`: Runtime dependencies (frozen)
- `requirements-dev.txt`: Dev/test tools (Pytest, Ruff, mypy, Bandit)

After adding dependencies:
```bash
poetry export -f requirements.txt --without-hashes -o requirements.txt
poetry export -f requirements.txt --without-hashes --only dev -o requirements-dev.txt
poetry run python scripts/check_requirements_sync.py
```

### 2. Setup Git Hooks

```bash
poetry run pre-commit install
poetry run pre-commit install --hook-type pre-push
poetry run pre-commit install --hook-type commit-msg
```

**What runs where:**

| Trigger | Checks | Speed |
|---------|--------|-------|
| **commit** | Ruff, pyupgrade, detect-secrets, .env/.txt sync | ~1s |
| **commit-msg** | Commitizen format (use `cz commit`) | instant |
| **pre-push** | mypy, Bandit, full pytest suite | ~30-60s |

Skip with `--no-verify` only if you know what you're doing (CI will catch it).

### 3. Environment

```bash
cp .env.example .env
```

For **host-based development** (not Docker), edit `.env`:

```env
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
NEO4J_URI=bolt://127.0.0.1:7687
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1
MINIO_ENDPOINT=127.0.0.1:9000
```

**Start databases only:**
```bash
# Option A: Spin up just the DB services from Compose
docker compose -f docker/compose.yml --env-file .env up -d db redis neo4j minio

# Option B: Run Postgres/Neo4j/Redis manually on the host
# (PostgreSQL 15, Neo4j 5, Redis 8 required)
```

### 4. Database Migrations

```bash
poetry run alembic upgrade head
```

**Schema versioning:**
- Migrations live in `migrations/versions/`
- Linear chain: `0001_initial` → `0002_*` → ...
- Rollback: `poetry run alembic downgrade base` (destructive)
- Verify: `tests/integration/migrations/test_schema_matches_models.py`

### 5. Start Services

**In separate terminals:**

```bash
# Terminal 1: API server (auto-reload)
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Terminal 2: Celery worker (routes tasks to sync_person, sync_relationship, backup_database)
poetry run celery -A app.celery.celery_app worker -l info --pool=solo \
  -Q celery,sync_person,sync_relationship,backup_database

# Terminal 3: Celery Beat (schedule daily backups at 00:00 Tehran time)
poetry run celery -A app.celery.celery_app beat --loglevel=info

# Terminal 4 (optional): Flower (task monitoring)
poetry run celery -A app.celery.celery_app flower --port=5555
```

**Note:** Without a running worker, Neo4j will not sync (Postgres writes still succeed though).

### 6. Run Tests

```bash
# Full suite with coverage
poetry run pytest -v --cov=app --cov-report=term-missing

# Single test file
poetry run pytest tests/e2e/routers/test_person_router.py -v

# Watch mode (with pytest-watch):
poetry run ptw --runner "pytest -v"
```

**Test structure:**
- `tests/unit/` → Entities, use cases, services (no I/O)
- `tests/integration/` → Database repos, Neo4j integration
- `tests/e2e/` → Full HTTP API via ASGI (Celery stubbed)

**Coverage gate:** ≥90% on `app/` (enforced in CI)

### 7. Code Quality

```bash
# Lint & format
poetry run ruff check .
poetry run ruff format --check .

# Type checking
poetry run mypy .

# Security scanning
poetry run bandit -r app -c pyproject.toml -ll

# Check all configs in sync
poetry run python scripts/check_env_example_sync.py
poetry run python scripts/check_requirements_sync.py
```

---

## API Reference

### REST Endpoints

Interactive docs: http://localhost:8001/api_docs

**Base path:** `/` (no `/api` prefix)

#### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | OAuth2 password flow → `{access_token, refresh_token}` |
| `/auth/refresh` | POST | Rotate refresh token → new `{access_token, refresh_token}` |
| `/auth/logout` | POST | Revoke current session |
| `/auth/logout-all` | POST | Revoke all sessions for user |
| `/auth/me` | GET | Get current user + roles/permissions |

#### Family Trees (Multi-Tenant)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/family-trees` | GET | List trees user is member of |
| `/family-trees` | POST | Create a tree (caller = owner) |
| `/family-trees/{tree_id}` | GET | Get tree details |
| `/family-trees/{tree_id}` | PUT | Update tree (name, etc.) |
| `/family-trees/{tree_id}` | DELETE | Delete tree (owner only) |
| `/family-trees/{tree_id}/members` | GET | List tree members + roles |
| `/family-trees/{tree_id}/members` | POST | Add member to tree |
| `/family-trees/{tree_id}/members/{user_id}` | DELETE | Remove member from tree |

#### Persons

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/family-trees/{tree_id}/persons` | GET | List persons in tree (paginated, filterable) |
| `/family-trees/{tree_id}/persons` | POST | Create person |
| `/family-trees/{tree_id}/persons/{id}` | GET | Get person details |
| `/family-trees/{tree_id}/persons/{id}` | PUT | Update person |
| `/family-trees/{tree_id}/persons/{id}` | DELETE | Delete person |
| `/family-trees/{tree_id}/persons/{id}/relation/{to_id}` | GET | Closest relationship (via Neo4j) |

**Dates:** Jalali `YYYY/MM/DD` (Persian calendar)

#### Marriages

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/family-trees/{tree_id}/marriages` | GET | List marriages (paginated, filterable) |
| `/family-trees/{tree_id}/marriages` | POST | Create marriage record |
| `/family-trees/{tree_id}/marriages/{id}` | GET | Get marriage details |
| `/family-trees/{tree_id}/marriages/{id}` | PUT | Update marriage |
| `/family-trees/{tree_id}/marriages/{id}/divorce` | POST | Record divorce |
| `/family-trees/{tree_id}/marriages/{id}` | DELETE | Delete marriage |

#### Media (Photos)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/family-trees/{tree_id}/media/upload` | POST | Upload photo → `photo_object_key` |
| `/media/{object_key}` | GET | Stream photo (serves `<img src>`) |

#### Excel Import/Export

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/family-trees/{tree_id}/excel/template` | GET | Download template |
| `/family-trees/{tree_id}/excel/preview` | POST | Preview before import |
| `/family-trees/{tree_id}/excel/import` | POST | Import Excel |
| `/family-trees/{tree_id}/excel/export` | POST | Export tree to Excel |

#### Users, Roles, Permissions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/users` | GET/POST | User CRUD (admin only) |
| `/roles` | GET/POST | Role CRUD |
| `/permissions` | GET | List all permissions |
| `/tickets` | GET/POST | Support tickets |

#### Health & Monitoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness probe (Postgres + Neo4j) → `{status: "ok"/"degraded"}` |
| `/health/neo4j` | GET | Neo4j-only health check |

---

### GraphQL Schema

**Endpoint:** `POST /graphql` (GraphiQL at http://localhost:8001/graphql)

Same operations as REST, but with GraphQL syntax:

```graphql
mutation {
  login(username: "admin", password: "admin") {
    accessToken
    refreshToken
  }
}

mutation {
  createFamilyTree(data: { name: "Karimi Family" }) {
    id
    name
  }
}

query {
  person(treeId: "tree_123", id: "person_456") {
    id
    name
    gender
    birthDate
    photos
  }
}

query {
  closestRelationship(treeId: "tree_123", fromId: "p1", toId: "p2") {
    distance
    path {
      id
      name
      relationshipType
    }
  }
}
```

**Auth:** Pass `Authorization: Bearer <access_token>` header (same as REST).

---

## Configuration

All settings are environment-based (`.env` file or shell variables).

### Essential Settings

```env
# Security
JWT_SECRET=your-32-char-minimum-secret-here
ENVIRONMENT=production  # local, development, staging, production

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=strongpass
POSTGRES_DB=family_tree

# Test database (MUST be separate)
POSTGRES_DB_TEST=family_tree_test

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4jpass

# Redis / Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Admin user (seeded on startup)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme  # Staging/production reject weak passwords
```

### Optional Settings

```env
# Token lifetimes
ACCESS_TOKEN_EXPIRE_MINUTES=5
REFRESH_TOKEN_EXPIRE_MINUTES=60

# CORS (comma-separated)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# GraphQL limits (defend against malicious queries)
GRAPHQL_MAX_DEPTH=10
GRAPHQL_MAX_ALIASES=15
GRAPHQL_MAX_TOKENS=2000

# MinIO / S3
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=family-tree
MINIO_BUCKETS=family-tree  # Comma-separated, auto-created

# Rate limiting
AUTH_RATE_LIMIT_PER_MINUTE=30

# Backups
BACKUP_DIR=/mnt/backups

# Flower monitoring
FLOWER_BASIC_AUTH=admin:admin

# Published ports (for Docker)
API_PORT=8001
FLOWER_PORT=5555
```

**Validation:**
- `JWT_SECRET` must be ≥32 chars (enforced at startup)
- Weak secrets (`admin`, `postgres`, etc.) rejected in `staging`/`production`
- `POSTGRES_DB_TEST` must differ from `POSTGRES_DB` (tests can't wipe app data)
- Changes to `AppSettings` must be reflected in `.env.example` (checked by CI)

---

## Testing & Quality

### Run Tests

```bash
# All tests with coverage report
poetry run pytest -v --cov=app --cov-report=term-missing

# Specific test file
poetry run pytest tests/unit/application/use_cases/test_login.py -v

# With xfail (expected failures)
poetry run pytest -v --runxfail
```

### Test Layout

```
tests/
  unit/                    # No database, fast
    application/
      use_cases/
      services/
    domain/
  integration/             # Real database, medium speed
    repositories/
    migrations/
  e2e/                     # Full HTTP API, Celery stubbed
    routers/
    graphql/
```

### Coverage Requirements

- **Gate:** ≥90% on `app/` (CI fails if lower)
- **Branches:** Aim for 85%+ branch coverage (harder to test)

**Generate report:**
```bash
poetry run pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Quality Checks

| Tool | Purpose | Command |
|------|---------|---------|
| **Ruff** | Lint + format | `poetry run ruff check . && poetry run ruff format .` |
| **mypy** | Type checking | `poetry run mypy .` |
| **Bandit** | Security scan | `poetry run bandit -r app -c pyproject.toml -ll` |
| **Commitizen** | Commit format | `poetry run cz commit` |

**Run all:**
```bash
poetry run ruff check . && poetry run ruff format . && \
poetry run mypy . && \
poetry run bandit -r app -c pyproject.toml -ll
```

---

## CI/CD Pipeline

### GitHub Actions (`ci.yml`)

Runs on every push/PR to `main`:

**Job 1: Quality** (2 min)
- Ruff lint & format
- mypy type check
- Bandit security scan
- `.env.example` sync check
- `requirements*.txt` sync check

**Job 2: Stack** (8 min)
- Build Docker images (runtime + ci)
- Spin up full Compose stack
- Run `alembic upgrade head`
- Create test database
- Run pytest with 90% coverage gate
- Verify production image has no test tools

### Local Simulation

```bash
# Simulate CI locally (slow, full suite)
cp .env.example .env
export APP_IMAGE_TARGET=ci
docker compose -f docker/compose.yml --env-file .env up --build -d
docker compose exec -T api pytest -v --cov=app --cov-fail-under=90
```

### Pre-push Hook

```bash
# Runs before pushing to origin (can be slow ~30-60s)
poetry run pytest -v
poetry run mypy .
poetry run bandit -r app -c pyproject.toml -ll
```

---

## Project Structure

### Directory Layout

```
family-tree-backend/
├── app/                          # Main application code
│   ├── application/              # Use cases, DTOs, services
│   │   ├── use_cases/            # One file per use case (login, create_person, etc.)
│   │   ├── services/             # Cross-cutting: authorization, excel, sync
│   │   ├── interfaces/           # Abstract interfaces (token service, UoW)
│   │   └── dto/                  # Data Transfer Objects for all domains
│   ├── domain/                   # Business logic, entities, rules
│   │   ├── entities/             # Person, Marriage, User, etc.
│   │   ├── repositories/         # Abstract repository interfaces
│   │   ├── exceptions/           # Domain-specific exceptions
│   │   ├── services/             # Domain services (marriage rules, password hashing)
│   │   └── shared/               # Common enums, DTOs, permissions
│   ├── infrastructure/           # Concrete implementations
│   │   ├── database/             # SQLAlchemy models, Alembic migrations
│   │   ├── repositories/         # SQL & Neo4j implementations
│   │   ├── services/             # JWT, password hashing, UoW, permission cache
│   │   ├── storage/              # MinIO S3-compatible client
│   │   └── utils/                # Mappers, logging, Neo4j helpers
│   ├── presentation/             # HTTP & GraphQL
│   │   ├── rest/                 # FastAPI routers, schemas, dependencies
│   │   ├── graphql/              # Strawberry schema, resolvers, auth
│   │   └── utils/                # Rate limiting, trace IDs, language detection
│   ├── celery/                   # Background tasks
│   │   └── tasks/                # Person sync, relationship sync, backups
│   ├── core/                     # App settings & configuration
│   └── main.py                   # FastAPI app factory, lifespan, middleware
├── tests/                        # Test suites
│   ├── unit/                     # No I/O, fast
│   ├── integration/              # Database integration
│   └── e2e/                      # HTTP API (Celery stubbed)
├── migrations/                   # Alembic SQL schema migrations
├── docker/                       # Dockerfile, Compose, entrypoint
├── bruno/                        # Bruno API client collection
├── scripts/                      # Utility scripts (env sync, requirements check)
├── pyproject.toml                # Poetry dependencies & config
├── pytest.ini                    # Pytest configuration
├── .env.example                  # Environment template
├── alembic.ini                   # Alembic configuration
└── README.md                     # This file
```

### Key Design Patterns

**Clean Architecture Layers:**
- **Entities** = Pure domain logic, no dependencies
- **Use Cases** = Orchestrate domain entities + repositories
- **Repositories** = Abstract interfaces, concrete SQL/Neo4j implementations
- **Presentation** = HTTP + GraphQL on top of use cases

**Single Responsibility:**
- One use case = one business action (e.g., `CreatePersonUseCase`)
- Services are injected via dependency injection
- Repositories hidden behind interfaces

**Async Throughout:**
- SQLAlchemy 2 async ORM with asyncpg
- All I/O is non-blocking (database, Redis, MinIO, Neo4j)
- Celery for heavy CPU work (Excel processing, backups)

---

## Troubleshooting

### Common Issues

#### 1. **Docker Build Fails**

**Error:** `no such file or directory: 'D:projectsftfamily-tree-backenddockercompose.dev.yml'`

**Solution:** This is a corrupt file created by Windows. Delete it:
```bash
rm "D:projectsftfamily-tree-backenddockercompose.dev.yml"
```

#### 2. **Neo4j Out of Sync**

**Symptom:** `closest-relationship` returns empty paths even after creating persons

**Cause:** Celery worker not running or task queue blocked

**Solution:**
```bash
# Check if worker is running
docker compose exec celery_worker celery -A app.celery.celery_app inspect active

# Restart worker
docker compose restart celery_worker

# Check Flower for failed tasks
open http://localhost:5555
```

#### 3. **Test Database Won't Delete**

**Error:** `FATAL: database "family_tree_test" is being accessed by other users`

**Solution:** Kill lingering connections:
```bash
docker compose exec db psql -U postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity \
   WHERE datname='family_tree_test'"
```

#### 4. **JWT Token Expired**

**Error:** `401 Unauthorized`

**Solution:** Get a new access token:
```bash
curl -X POST http://localhost:8001/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "..."}'
```

#### 5. **MinIO Buckets Not Created**

**Symptom:** Photo upload fails with 404

**Solution:** Restart API to trigger bootstrap:
```bash
docker compose restart api
```

#### 6. **Rate Limiting Blocks Logins**

**Error:** `429 Too Many Requests` on `/auth/login`

**Cause:** Redis unreachable or rate limit exhausted (default 30/min)

**Solution:**
```env
# In .env, increase limit
AUTH_RATE_LIMIT_PER_MINUTE=60

# Or restart Redis
docker compose restart redis
```

#### 7. **mypy Complains About Missing Stubs**

**Error:** `Cannot find implementation or library stub for module named 'X'`

**Solution:** Most are OK to ignore. Check `.mypy.ini`:
```ini
ignore_missing_imports = true
```

### Debug Logging

**Enable debug output:**
```bash
# FastAPI
poetry run uvicorn app.main:app --reload --log-level debug

# Celery
poetry run celery -A app.celery.celery_app worker --loglevel debug

# Or in code:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Check

```bash
# Full health (Postgres + Neo4j)
curl http://localhost:8001/health

# Response:
# {
#   "status": "ok",
#   "postgres": "ok",
#   "neo4j": "ok"
# }

# If degraded:
# HTTP 503 with status: "degraded"
```

---

## Contributing

1. **Branch:** Create from `main` with descriptive name (e.g., `feat/closest-relationship-cache`)
2. **Commit:** Use `poetry run cz commit` for structured messages
3. **Push:** Pre-push hooks run tests + type check + security scan
4. **PR:** Include test coverage, update docs
5. **CI:** GitHub Actions must pass before merge

---

## Performance Notes

### N+1 Query Prevention

- Use `selectinload()` / `joinedload()` in SQLAlchemy
- Excel export uses optimized batch queries
- Tree member listing uses single JOIN (not loop)

### Graph Sync Lag

- Neo4j is eventually consistent (Celery async tasks)
- Expect ~100ms-1s after Postgres write
- For real-time graph queries, query Postgres first, fall back to Neo4j

### Caching Opportunities

- Person photos: Presigned URLs cached in browser (1 hour default)
- Permission checks: Cached in-memory per request
- Future: Redis caching for hot graph paths

---

## Roadmap

- [ ] Redis caching for frequently-accessed family hierarchies
- [ ] OpenTelemetry metrics and distributed tracing
- [ ] Batch relationship import (CSV parsing)
- [ ] Photo cropping / thumbnail generation
- [ ] Family tree sharing (time-limited links)

---

## License

MIT License — See [LICENSE](LICENSE)

---

## Support

**Maintainer:** Arash Alfooneh  
**Email:** arash.alfooneh@gmail.com

**Issues:** Create a GitHub issue with reproduction steps and environment details.

---

**Last Updated:** August 2026
