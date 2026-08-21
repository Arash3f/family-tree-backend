from uuid import UUID

from celery import shared_task

from app.domain.shared.dto.family_tree_dto import (
    DeleteRelationshipDTO,
    DeleteSpouseRelationshipDTO,
    ParentRelationshipDTO,
    SpouseRelationshipDTO,
)
from app.infrastructure.database.neo4j.neo4j import run_celery_coro
from app.infrastructure.repositories.neo4j_family_tree_repository import (
    Neo4jFamilyTreeRepository,
)

# Module-level singleton shared across task invocations; each task goes through
# ``run_celery_coro`` so the Neo4j client is closed between asyncio.run calls.
repo = Neo4jFamilyTreeRepository()


async def _create_parent_relationship(data: ParentRelationshipDTO) -> None:
    await repo.create_parent_relationship(data=data)


async def _delete_parent_relationship(data: DeleteRelationshipDTO) -> None:
    await repo.delete_parent_relationship(data=data)


async def _create_spouse_relationship(data: SpouseRelationshipDTO) -> None:
    await repo.create_spouse_relationship(data=data)


async def _delete_spouse_relationship(data: DeleteSpouseRelationshipDTO) -> None:
    await repo.delete_spouse_relationship(data=data)


@shared_task(
    name="sync.relationship.parent",
    bind=True,
    max_retries=5,
    retry_backoff=True,
    autoretry_for=(ConnectionError, TimeoutError, RuntimeError),
)
def sync_parent_relationship(self, parent_id: str, child_id: str):
    data = ParentRelationshipDTO(
        parent_id=UUID(str(parent_id)),
        child_id=UUID(str(child_id)),
    )
    run_celery_coro(_create_parent_relationship(data))


@shared_task(
    name="sync.relationship.parent.delete",
    bind=True,
    max_retries=5,
    retry_backoff=True,
    autoretry_for=(ConnectionError, TimeoutError, RuntimeError),
)
def sync_parent_rel_delete(self, parent_id: str, child_id: str):
    data = DeleteRelationshipDTO(
        parent_id=UUID(str(parent_id)),
        child_id=UUID(str(child_id)),
    )
    run_celery_coro(_delete_parent_relationship(data))


@shared_task(
    name="sync.relationship.spouse",
    bind=True,
    max_retries=5,
    retry_backoff=True,
    autoretry_for=(ConnectionError, TimeoutError, RuntimeError),
)
def sync_spouse_relationship(self, person_id_1: str, person_id_2: str):
    data = SpouseRelationshipDTO(
        person_id_1=UUID(str(person_id_1)),
        person_id_2=UUID(str(person_id_2)),
    )
    run_celery_coro(_create_spouse_relationship(data))


@shared_task(
    name="sync.relationship.spouse.delete",
    bind=True,
    max_retries=5,
    retry_backoff=True,
    autoretry_for=(ConnectionError, TimeoutError, RuntimeError),
)
def sync_spouse_relationship_delete(self, person_id_1: str, person_id_2: str):
    data = DeleteSpouseRelationshipDTO(
        person_id_1=UUID(str(person_id_1)),
        person_id_2=UUID(str(person_id_2)),
    )
    run_celery_coro(_delete_spouse_relationship(data))
