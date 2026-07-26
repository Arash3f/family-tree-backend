from datetime import date
from unittest.mock import MagicMock, patch
from uuid import UUID

from app.application.services.family_tree_sync_service import FamilyTreeSyncService
from app.domain.entities.person import Gender, Person


def _person(**kwargs) -> Person:
    defaults = {
        "id": UUID(int=10),
        "name": "Ali",
        "gender": Gender.MALE,
        "birth_date": date(2000, 1, 1),
        "death_date": None,
        "father_id": None,
        "mother_id": None,
    }
    defaults.update(kwargs)
    return Person(**defaults)


def test_upsert_person_with_parents_enqueues_chain():
    service = FamilyTreeSyncService()
    person = _person(father_id=UUID(int=1), mother_id=UUID(int=2))

    with (
        patch(
            "app.application.services.family_tree_sync_service.sync_person_upsert"
        ) as upsert,
        patch(
            "app.application.services.family_tree_sync_service.sync_parent_relationship"
        ) as parent,
        patch("app.application.services.family_tree_sync_service.chain") as chain_mock,
    ):
        upsert.si.return_value = "upsert"
        parent.si.side_effect = ["f", "m"]
        chain_mock.return_value.apply_async = MagicMock()

        service.upsert_person(person)

        chain_mock.assert_called_once_with("upsert", "f", "m")
        chain_mock.return_value.apply_async.assert_called_once()


def test_update_person_parent_change_deletes_and_creates():
    service = FamilyTreeSyncService()
    person = _person(father_id=UUID(int=3), mother_id=None)

    with (
        patch(
            "app.application.services.family_tree_sync_service.sync_person_upsert"
        ) as upsert,
        patch(
            "app.application.services.family_tree_sync_service.sync_parent_rel_delete"
        ) as delete_rel,
        patch(
            "app.application.services.family_tree_sync_service.sync_parent_relationship"
        ) as parent,
        patch("app.application.services.family_tree_sync_service.chain") as chain_mock,
    ):
        upsert.si.return_value = "upsert"
        delete_rel.si.return_value = "del"
        parent.si.return_value = "create"
        chain_mock.return_value.apply_async = MagicMock()

        service.update_person(
            person, old_father_id=UUID(int=1), old_mother_id=None
        )

        chain_mock.assert_called_once_with("upsert", "del", "create")


def test_delete_and_spouse_helpers():
    service = FamilyTreeSyncService()

    with patch(
        "app.application.services.family_tree_sync_service.sync_person_delete"
    ) as delete:
        service.delete_person(UUID(int=1))
        delete.delay.assert_called_once_with(str(UUID(int=1)))

    with patch(
        "app.application.services.family_tree_sync_service.sync_spouse_relationship"
    ) as spouse:
        service.upsert_spouse(UUID(int=1), UUID(int=2))
        spouse.apply_async.assert_called_once()

    with patch(
        "app.application.services.family_tree_sync_service.sync_spouse_relationship_delete"
    ) as spouse_del:
        service.remove_spouse(UUID(int=1), UUID(int=2))
        spouse_del.delay.assert_called_once()

    with (
        patch(
            "app.application.services.family_tree_sync_service.sync_spouse_relationship_delete"
        ) as spouse_del,
        patch(
            "app.application.services.family_tree_sync_service.sync_spouse_relationship"
        ) as spouse,
        patch("app.application.services.family_tree_sync_service.chain") as chain_mock,
    ):
        spouse_del.si.return_value = "del"
        spouse.si.return_value = "add"
        chain_mock.return_value.apply_async = MagicMock()
        service.replace_spouse(
            old_person_id_1=UUID(int=1),
            old_person_id_2=UUID(int=2),
            new_person_id_1=UUID(int=3),
            new_person_id_2=UUID(int=4),
        )
        chain_mock.assert_called_once_with("del", "add")


def test_enqueue_swallows_exceptions(caplog):
    service = FamilyTreeSyncService()
    service._enqueue(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert "Failed to enqueue Neo4j sync task after commit" in caplog.text
