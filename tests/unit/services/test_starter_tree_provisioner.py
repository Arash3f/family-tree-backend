from collections import Counter
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.application.services.starter_tree_provisioner import StarterTreeProvisioner
from app.domain.entities.person import Person
from app.domain.shared.starter_trees import STARTER_TREE_SPECS


async def _assign_id(entity):
    entity.id = uuid4()
    return entity


@pytest.mark.asyncio
async def test_provisions_both_hardcoded_workbooks_with_relationships():
    uow = MagicMock()
    uow.family_trees.create = AsyncMock(side_effect=_assign_id)
    uow.tree_memberships.create = AsyncMock(side_effect=lambda membership: membership)
    uow.persons.create = AsyncMock(side_effect=_assign_id)
    uow.persons.update = AsyncMock(side_effect=lambda *, person: person)
    uow.marriages.create = AsyncMock(side_effect=_assign_id)
    sync_service = MagicMock()
    provisioner = StarterTreeProvisioner(sync_service=sync_service)

    result = await provisioner.provision_for_user(
        uow,
        owner_user_id=UUID(int=42),
    )

    assert [tree.name for tree in result.trees] == [
        spec.default_name for spec in STARTER_TREE_SPECS
    ]
    assert len(result.trees) == 2
    assert len(result.persons) == 40
    assert len(result.marriages) == 16
    assert Counter(person.tree_id for person in result.persons) == {
        tree.safe_id: 20 for tree in result.trees
    }
    assert Counter(marriage.tree_id for marriage in result.marriages) == {
        tree.safe_id: 8 for tree in result.trees
    }

    english_people = _people_for_tree(result.persons, result.trees[0].safe_id)
    ali = next(person for person in english_people if person.name == "Ali")
    assert {
        person.name for person in english_people if person.safe_id in ali.parent_ids
    } == {
        "Reza",
        "Maryam",
    }
    assert ali.marriage_id is not None

    persian_people = _people_for_tree(result.persons, result.trees[1].safe_id)
    assert {person.name for person in persian_people} >= {"علی", "رضا", "مریم"}

    provisioner.sync_after_commit(result)
    assert sync_service.upsert_person.call_count == 40
    assert sync_service.upsert_spouse.call_count == 16


def _people_for_tree(persons: list[Person], tree_id: UUID) -> list[Person]:
    return [person for person in persons if person.tree_id == tree_id]
