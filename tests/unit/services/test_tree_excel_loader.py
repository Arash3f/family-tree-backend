from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.services.tree_excel_loader import load_all_tree_persons
from app.domain.entities.person import Gender, Person
from app.domain.shared.dto.pagination_dto import PaginatedResult


def _person(name: str, *, person_id=None) -> Person:
    return Person(
        id=person_id or uuid4(),
        name=name,
        gender=Gender.MALE,
        tree_id=uuid4(),
        birth_date=None,
        death_date=None,
        family_name=None,
        birth_place=None,
        death_place=None,
        notes=None,
        parents=[],
        marriage_id=None,
        photo_object_key=None,
    )


@pytest.mark.asyncio
async def test_load_all_tree_persons_dedupes_unstable_pages():
    tree_id = uuid4()
    shared_id = uuid4()
    first = _person("رضا", person_id=shared_id)
    first.tree_id = tree_id
    duplicate = _person("رضا", person_id=shared_id)
    duplicate.tree_id = tree_id
    other = _person("علی", person_id=uuid4())
    other.tree_id = tree_id

    page1 = PaginatedResult(items=[first, other], total=2, page=1, page_size=100)
    # Simulate a flaky second page that repeats a row already returned.
    page2 = PaginatedResult(items=[duplicate], total=2, page=2, page_size=100)

    uow = SimpleNamespace()
    uow.persons = SimpleNamespace(
        get_list_by_filter=AsyncMock(side_effect=[page1, page2])
    )

    loaded = await load_all_tree_persons(uow, tree_id)

    assert len(loaded) == 2
    assert [person.safe_id for person in loaded].count(shared_id) == 1
