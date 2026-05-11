# Family Tree API

A robust, production-ready Family Tree management system built with FastAPI, following Clean Architecture principles. This project leverages the power of PostgreSQL for transactional data and Neo4j for complex graph-based relationship traversals.

---

# 🚀 Features

- **Hybrid Data Storage**: Seamless integration of Relational (PostgreSQL) and Graph (Neo4j) databases.
- **Advanced Graph Queries**: Find the shortest path (closest relationship) between any two individuals using Neo4j's Cypher.
- **Clean Architecture**: Strict separation of concerns (Presentation, Application, Domain, Infrastructure).
- **Background Tasks**: Automated daily backups and heavy Neo4j operations via Celery and Redis.
- **Containerized**: Fully Dockerized environment for easy deployment and scaling.
- **Database Migrations**: Managed by Alembic for PostgreSQL schema versioning.

---

# 🛠 Tech Stack

- **Framework**: FastAPI
- **Databases**: PostgreSQL (SQL), Neo4j (Graph)
- **Task** Queue: Celery + Redis
- **Migrations**: Alembic
- **Server**: Uvicorn / Gunicorn
- **DevOps**: Docker & Docker Compose
- **Testing**: Pytest

---

# 🏗 System Architecture Overview

The system follows a layered approach where the **Application Layer** orchestrates how data is fetched or persisted based on the specific use case.

## Hybrid Persistence Strategy

Unlike traditional systems, this API uses a multi-database strategy:

1. **PostgreSQL Only Requests**: Used for standard CRUD operations, authentication, and metadata management where ACID compliance is critical.
2. **Neo4j Only Requests**: Used for pure graph exploration, identifying relationship types, and structural tree analysis.
3. **Hybrid Requests**: For person-related entities, the system interacts with both databases. It ensures transactional integrity in PostgreSQL while simultaneously reflecting the relationship structure in Neo4j to enable high-performance graph traversals.

## Layers Structure

- **Presentation**: API endpoints, Request/Response schemas (DTOs).
- **Application**: Use cases, business logic orchestration, and service coordination.
- **Domain**: Core entities, value objects, and repository interfaces.
- **Infrastructure**: Database clients (Postgres/Neo4j), Repository implementations and external services.
- **Celery**: Celery tasks
---

# 📋 Data Storage Strategy

The system uses **two databases with different responsibilities**.

## PostgreSQL

Used for:

- Core entity storage
- Structured relational data
- Transactions
- Migration management


## Neo4j

Used for:

- Modeling family relationships
- Graph traversal queries
- Finding relationship paths
- Calculating **closest relationship between two individuals**

Person data is also stored in Neo4j to simplify traversal queries and avoid cross-database joins.

---

# 🏃 Running the Project

## 1. Using Docker (Recommended)

The easiest way to spin up the entire stack including databases and workers:

```
docker-compose up --build
```

Once the Docker Compose stack is running, the following services will be available:
- FastAPI Application: http://localhost:8001
- FastAPI Interactive Docs (Swagger UI): http://localhost:8001/api_docs
- FastAPI Alternative Docs (ReDoc): http://localhost:8001/redoc
- Neo4j Browser: http://localhost:7474
- PostgreSQL: Accessible on port 5432 from within the Docker network.
- Redis: Accessible on port 6379 from within the Docker network.
- Celery: Celery flower: http://localhost:5555

##  2. Local Development (Manual)

If you prefer running the API locally with uvicorn (ensure Postgres, Neo4j, and Redis are running):

### 1. Install dependencies:
```
pip install -r requirements.txt
```
### 2. Set Environment Variables:
Create a .env file in the project root based on .env.example.

### 3. Run Migrations:
```
alembic upgrade head
```

### 4. Run Celery Worker & Beat:
```
poetry run celery -A app.celery.celery_app worker -l info --pool=solo
poetry run celery -A app.celery.celery_app beat --loglevel=info
```

### 5. Start the API with Uvicorn:
```
celery -A app.celery.celery_app flower --port=5555
```

### 6. Run Celery Flower:
```
poetry run celery -A app.celery.celery_app worker -l info --pool=solo
poetry run celery -A app.celery.celery_app beat --loglevel=info
```

## ! Seeding Initial Data

A sample file is provided to simplify adding initial family tree data.

1. Open `seed_items.sample` and complete the data lists.
2. In `main.py`, uncomment the following line:
```python
# await seed_initial_items(uow=uow)
```
3. Run the application to populate the database with the initial data.
---

## ⏳ Background Tasks & Maintenance
The system uses Celery for handling asynchronous and scheduled tasks.

### Key Background Tasks

- **Graph Synchronization**: Whenever a person is created or updated in PostgreSQL, a Celery task is triggered to ensure the Neo4j node is synchronized.
- **Daily Backups**: A scheduled Celery beat task triggers every midnight to dump PostgreSQL and Neo4j data to a designated backup storage.

---

# 🧪 Running Tests

Execute tests using:

```
pytest .
```

---

# 🗺 Roadmap / Pending Work

The following features are planned or not yet fully implemented:

- ✅ Update ReadMy
- ✅ Add github actions
- ✅ Initial item implementation
- ☐ Monitoring and logging improvements
- ☐ Graph caching with redis
- ✅ Celery Flow for Task Monitor
- ✅ Daily backup neo4j
- ☐ Add death date field to Person
- ✅ Fix mypy error in pre commit
- ☐ Neo4j Integration test
- ☐ Fix docker action errors!
- ☐ E2E test:
  - ☐ permission
  - ☐ auth
  - ☐ role
  - ☐ user
  - ☐ person (+Neo4j)
  - ☐ marriage (+Neo4j)
- ...

---


# License

This project is intended for educational and development purposes.

---
Developed with ❤️ by Arash Alfooneh.
