from datetime import datetime, timezone

from celery import shared_task

from app.domain.shared.dto.family_tree_dto import PersonIdDTO, PersonUpsertDTO
from app.infrastructure.repositories.neo4j_family_tree_repository import (
    Neo4jFamilyTreeRepository,
)

repo = Neo4jFamilyTreeRepository()


@shared_task(
    name="sync.person.upsert",
    bind=True,
    max_retries=5,
    retry_backoff=True,
    retry_jitter=True,
)
def sync_person_upsert(self, payload: PersonUpsertDTO):
    payload = PersonUpsertDTO.model_validate(payload)

    try:
        now_utc = datetime.now(timezone.utc)

        payload.created_at = now_utc
        payload.updated_at = now_utc

        repo.upsert_person(data=payload)

    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(name="sync.person.delete", bind=True, max_retries=5, retry_backoff=True)
def sync_person_delete(self, person_id: int):
    data = PersonIdDTO(id=person_id)
    try:
        repo.delete_person(data=data)
    except Exception as exc:
        raise self.retry(exc=exc)
