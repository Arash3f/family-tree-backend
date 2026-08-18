import asyncio
from datetime import UTC, datetime
from uuid import UUID

from celery import shared_task

from app.domain.shared.dto.family_tree_dto import PersonIdDTO, PersonUpsertDTO
from app.infrastructure.repositories.neo4j_family_tree_repository import (
    Neo4jFamilyTreeRepository,
)

# Module-level singleton, shared across task invocations within a worker
# process -- same pattern as before this migration.
#
# Event-loop note: Celery tasks here are plain sync `def`s with no asyncio
# event loop of their own, so we bridge into the now-async repository with
# `asyncio.run(...)` per task invocation, the same pattern used by
# app/celery/tasks/reconcile_neo4j.py for async Postgres access. Each
# `asyncio.run()` call creates a new event loop and tears it down on return,
# while `repo` (and the `neo4j_client` driver it lazily creates on first use,
# see app/infrastructure/database/neo4j/neo4j.py) persists across those
# calls. This is safe: the neo4j driver's internal async synchronization
# primitives have been based on Python 3.11-style lazy loop binding since
# driver 5.4.0 (see neo4j-python-driver changelog, fixing GH issue #868 --
# "future belongs to a different loop"), meaning the driver binds to
# whichever loop is *currently running* on each operation rather than
# permanently latching onto the loop active at construction/first-use time.
# This project pins `neo4j>=6.2.0,<7.0.0`, well past that fix. Reuse is safe
# for SEQUENTIAL asyncio.run() calls (never two loops touching the driver
# concurrently), which matches how Celery executes these tasks one at a time
# within a worker process.
repo = Neo4jFamilyTreeRepository()


async def _upsert_person(data: PersonUpsertDTO) -> None:
    await repo.upsert_person(data=data)


async def _delete_person(data: PersonIdDTO) -> None:
    await repo.delete_person(data=data)


@shared_task(
    name="sync.person.upsert",
    bind=True,
    max_retries=5,
    retry_backoff=True,
    retry_jitter=True,
    autoretry_for=(ConnectionError, TimeoutError, RuntimeError),
)
def sync_person_upsert(self, payload: dict):
    data = PersonUpsertDTO.model_validate(payload)
    now_utc = datetime.now(UTC)
    data.created_at = now_utc
    data.updated_at = now_utc
    asyncio.run(_upsert_person(data))


@shared_task(
    name="sync.person.delete",
    bind=True,
    max_retries=5,
    retry_backoff=True,
    autoretry_for=(ConnectionError, TimeoutError, RuntimeError),
)
def sync_person_delete(self, person_id: str):
    data = PersonIdDTO(id=UUID(str(person_id)))
    asyncio.run(_delete_person(data))
