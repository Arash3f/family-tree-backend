from uuid import UUID

from celery import shared_task

from app.domain.shared.dto.family_tree_dto import (
    DeleteRelationshipDTO,
    DeleteSpouseRelationshipDTO,
    ParentRelationshipDTO,
    SpouseRelationshipDTO,
)
from app.infrastructure.repositories.neo4j_family_tree_repository import (
    Neo4jFamilyTreeRepository,
)

repo = Neo4jFamilyTreeRepository()


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
    repo.create_parent_relationship(data=data)


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
    repo.delete_parent_relationship(data=data)


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
    repo.create_spouse_relationship(data=data)


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
    repo.delete_spouse_relationship(data=data)
