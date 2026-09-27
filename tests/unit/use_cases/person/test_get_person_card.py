from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.application.use_cases.person.get_person_card_use_case import (
    GetPersonCardUseCase,
)
from app.domain.entities.marriage import Marriage
from app.domain.entities.person import Gender, ParentLink, Person
from app.domain.shared.dto.common_dto import IdDTO


def _photo_service():
    service = MagicMock()

    def media_url(key):
        return f"media:{key}" if key else None

    service.media_url = MagicMock(side_effect=media_url)
    return service


def _person(
    person_id: int,
    *,
    name: str,
    gender: Gender = Gender.MALE,
    parents: list[ParentLink] | None = None,
    photo_key: str | None = None,
) -> Person:
    return Person(
        id=UUID(int=person_id),
        tree_id=UUID(int=7),
        name=name,
        gender=gender,
        birth_date=date(1990, 1, 1),
        parents=parents or [],
        photo_object_key=photo_key,
    )


@pytest.mark.asyncio
async def test_get_person_card_assembles_relations(mock_uow):
    root = _person(1, name="Root")
    child = _person(
        2,
        name="Child",
        gender=Gender.FEMALE,
        parents=[ParentLink(parent_id=UUID(int=1))],
    )
    spouse = _person(3, name="Spouse", gender=Gender.FEMALE)
    marriage = Marriage(
        id=UUID(int=9),
        tree_id=UUID(int=7),
        spouse_a_id=UUID(int=1),
        spouse_b_id=UUID(int=3),
        married_at=date(2010, 1, 1),
    )

    mock_uow.persons.get_in_tree_or_raise = AsyncMock(return_value=root)
    mock_uow.persons.get_by_tree_id = AsyncMock(return_value=[root, child, spouse])
    mock_uow.marriages.get_by_person_ids = AsyncMock(return_value=[marriage])

    use_case = GetPersonCardUseCase(mock_uow, _photo_service())
    card = await use_case.execute(IdDTO(id=UUID(int=1)), tree_id=UUID(int=7))

    assert card.person.name == "Root"
    assert len(card.marriages) == 1
    assert card.marriages[0].spouse is not None
    assert card.marriages[0].spouse.name == "Spouse"
    assert card.descendants.total.total == 1
    assert card.descendants.generations[0].generation == 1
    assert card.descendants.generations[0].people[0].name == "Child"

    mock_uow.persons.get_in_tree_or_raise.assert_awaited_once_with(
        person_id=UUID(int=1), tree_id=UUID(int=7)
    )
    mock_uow.persons.get_by_tree_id.assert_awaited_once_with(UUID(int=7))
    mock_uow.marriages.get_by_person_ids.assert_awaited_once_with([UUID(int=1)])
