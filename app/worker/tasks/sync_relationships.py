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
)
def sync_parent_relationship(self, parent_id: int, child_id: int):
    data = ParentRelationshipDTO(parent_id=parent_id, child_id=child_id)
    try:
        repo.create_parent_relationship(data=data)
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(
    name="sync.relationship.parent.delete",
    bind=True,
    max_retries=5,
    retry_backoff=True,
)
def sync_parent_rel_delete(self, parent_id: int, child_id: int):
    data = DeleteRelationshipDTO(child_id=parent_id, parent_id=child_id)
    try:
        repo.delete_parent_relationship(data=data)
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(
    name="sync.relationship.spouse",
    bind=True,
    max_retries=5,
    retry_backoff=True,
)
def sync_spouse_relationship(self, person_id_1: int, person_id_2: int):
    data = SpouseRelationshipDTO(person_id_1=person_id_1, person_id_2=person_id_2)
    try:
        repo.create_spouse_relationship(data=data)
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(
    name="sync.relationship.spouse.delete",
    bind=True,
    max_retries=5,
    retry_backoff=True,
)
def sync_spouse_relationship_delete(self, person_id_1: int, person_id_2: int):
    data = DeleteSpouseRelationshipDTO(person_id_1=person_id_1, person_id_2=person_id_2)
    try:
        repo.delete_spouse_relationship(data=data)
    except Exception as exc:
        raise self.retry(exc=exc)
