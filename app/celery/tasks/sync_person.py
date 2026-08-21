from datetime import UTC, datetime
from uuid import UUID

from celery import shared_task

from app.domain.shared.dto.family_tree_dto import PersonIdDTO, PersonUpsertDTO
from app.infrastructure.database.neo4j.neo4j import run_celery_coro
from app.infrastructure.repositories.neo4j_family_tree_repository import (
    Neo4jFamilyTreeRepository,
)

# Module-level singleton, shared across task invocations within a worker
# process. Each task runs through ``run_celery_coro``, which closes the shared
# Neo4j client after ``asyncio.run`` so the next task does not reuse a driver
# bound to a dead event loop.
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
    run_celery_coro(_upsert_person(data))


@shared_task(
    name="sync.person.delete",
    bind=True,
    max_retries=5,
    retry_backoff=True,
    autoretry_for=(ConnectionError, TimeoutError, RuntimeError),
)
def sync_person_delete(self, person_id: str):
    data = PersonIdDTO(id=UUID(str(person_id)))
    run_celery_coro(_delete_person(data))
