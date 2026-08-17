from uuid import UUID
import logging

from celery import chain

from app.celery.tasks.sync_person import sync_person_delete, sync_person_upsert
from app.celery.tasks.sync_relationships import (
    sync_parent_rel_delete,
    sync_parent_relationship,
    sync_spouse_relationship,
    sync_spouse_relationship_delete,
)
from app.domain.entities.person import Person

logger = logging.getLogger(__name__)


class FamilyTreeSyncService:
    """Dispatches Neo4j sync work after Postgres commits."""

    def _enqueue(self, dispatch) -> None:
        try:
            dispatch()
        except (OSError, RuntimeError) as e:
            logger.exception("Failed to enqueue Neo4j sync task after commit: %s", e)

    def upsert_person(self, person: Person) -> None:
        payload = {
            "id": str(person.safe_id),
            "full_name": person.name,
            "gender": person.gender.value.upper(),
            "birth_date": person.birth_date.isoformat() if person.birth_date else None,
            "death_date": person.death_date.isoformat() if person.death_date else None,
            "tree_id": str(person.tree_id),
        }

        tasks = [sync_person_upsert.si(payload)]

        for parent_id in person.parent_ids:
            tasks.append(
                sync_parent_relationship.si(str(parent_id), str(person.safe_id))
            )

        self._enqueue(lambda: chain(*tasks).apply_async())

    def update_person(
        self,
        person: Person,
        *,
        old_parent_ids: set[UUID],
    ) -> None:
        payload = {
            "id": str(person.safe_id),
            "full_name": person.name,
            "gender": person.gender.value.upper(),
            "birth_date": person.birth_date.isoformat() if person.birth_date else None,
            "death_date": person.death_date.isoformat() if person.death_date else None,
            "tree_id": str(person.tree_id),
        }

        tasks = [sync_person_upsert.si(payload)]
        new_parent_ids = set(person.parent_ids)

        for parent_id in old_parent_ids - new_parent_ids:
            tasks.append(sync_parent_rel_delete.si(str(parent_id), str(person.safe_id)))

        for parent_id in new_parent_ids - old_parent_ids:
            tasks.append(
                sync_parent_relationship.si(str(parent_id), str(person.safe_id))
            )

        self._enqueue(lambda: chain(*tasks).apply_async())

    def delete_person(self, person_id: UUID) -> None:
        self._enqueue(lambda: sync_person_delete.delay(str(person_id)))

    def upsert_spouse(self, person_id_1: UUID, person_id_2: UUID) -> None:
        # Retries on the task heal races where person nodes are not yet upserted
        self._enqueue(
            lambda: sync_spouse_relationship.apply_async(
                args=[str(person_id_1), str(person_id_2)],
                countdown=1,
            )
        )

    def remove_spouse(self, person_id_1: UUID, person_id_2: UUID) -> None:
        self._enqueue(
            lambda: sync_spouse_relationship_delete.delay(
                str(person_id_1), str(person_id_2)
            )
        )

    def replace_spouse(
        self,
        *,
        old_person_id_1: UUID,
        old_person_id_2: UUID,
        new_person_id_1: UUID,
        new_person_id_2: UUID,
    ) -> None:
        tasks = [
            sync_spouse_relationship_delete.si(
                str(old_person_id_1), str(old_person_id_2)
            ),
            sync_spouse_relationship.si(str(new_person_id_1), str(new_person_id_2)),
        ]
        self._enqueue(lambda: chain(*tasks).apply_async())
