from uuid import UUID
from datetime import date

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.application.dto.person.person_create_dto import (
    ParentLinkDTO,
    PersonCreateMapper,
)
from app.application.use_cases.person.create_person_use_case import CreatePersonUseCase
from app.domain.entities.person import Gender, ParentRelationshipType


def _photo_service():
    service = MagicMock()
    service.ensure_object_exists = AsyncMock()
    service.presign = AsyncMock(return_value=None)
    return service


@pytest.mark.asyncio
async def test_create_person_success_with_parents(mock_uow):
    dto = MagicMock()
    dto.name = "Ali"
    dto.gender = Gender.MALE
    dto.birth_date = date(2000, 1, 1)
    dto.death_date = None
    dto.parents = [
        ParentLinkDTO(parent_id=UUID(int=1)),
        ParentLinkDTO(parent_id=UUID(int=2)),
    ]
    dto.marriage_id = None
    dto.photo_object_key = None

    parent = MagicMock()
    created_person = MagicMock()
    created_person.photo_object_key = None

    mock_uow.family_trees.get_or_raise = AsyncMock()
    mock_uow.persons.get_in_tree_or_raise = AsyncMock(return_value=parent)
    mock_uow.persons.create = AsyncMock(return_value=created_person)

    expected_response = MagicMock()
    sync_service = MagicMock()
    photo_service = _photo_service()

    with patch.object(
        PersonCreateMapper, "to_response", return_value=expected_response
    ) as mapper_mock:
        use_case = CreatePersonUseCase(
            mock_uow, photo_service, sync_service=sync_service
        )
        result = await use_case.execute(dto, tree_id=UUID(int=7))

    assert result == expected_response

    mock_uow.persons.get_in_tree_or_raise.assert_any_await(
        person_id=UUID(int=1), tree_id=UUID(int=7)
    )
    mock_uow.persons.get_in_tree_or_raise.assert_any_await(
        person_id=UUID(int=2), tree_id=UUID(int=7)
    )

    mock_uow.persons.create.assert_awaited_once()

    mock_uow.commit.assert_awaited_once()
    sync_service.upsert_person.assert_called_once_with(created_person)

    mapper_mock.assert_called_once_with(created_person, photo_url=None)

    assert mock_uow.persons.create.await_args is not None
    created_entity = mock_uow.persons.create.await_args.args[0]
    assert created_entity.name == "Ali"
    assert created_entity.gender == Gender.MALE
    assert created_entity.parent_ids == [UUID(int=1), UUID(int=2)]


@pytest.mark.asyncio
async def test_create_person_allows_any_parent_gender(mock_uow):
    dto = MagicMock()
    dto.name = "Ali"
    dto.gender = Gender.MALE
    dto.birth_date = date(2000, 1, 1)
    dto.death_date = None
    dto.parents = [
        ParentLinkDTO(
            parent_id=UUID(int=1),
            relationship_type=ParentRelationshipType.ADOPTIVE,
        )
    ]
    dto.marriage_id = None
    dto.photo_object_key = None

    parent = MagicMock()
    parent.gender = Gender.FEMALE
    created_person = MagicMock()
    created_person.photo_object_key = None

    mock_uow.family_trees.get_or_raise = AsyncMock()
    mock_uow.persons.get_in_tree_or_raise = AsyncMock(return_value=parent)
    mock_uow.persons.create = AsyncMock(return_value=created_person)

    with patch.object(PersonCreateMapper, "to_response", return_value=MagicMock()):
        use_case = CreatePersonUseCase(
            mock_uow, _photo_service(), sync_service=MagicMock()
        )
        await use_case.execute(dto, tree_id=UUID(int=7))

    mock_uow.persons.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_person_without_parents(mock_uow):
    dto = MagicMock()
    dto.name = "Ali"
    dto.gender = Gender.MALE
    dto.birth_date = date(2000, 1, 1)
    dto.death_date = None
    dto.parents = []
    dto.marriage_id = None
    dto.photo_object_key = None

    created_person = MagicMock()
    created_person.photo_object_key = None

    mock_uow.family_trees.get_or_raise = AsyncMock()
    mock_uow.persons.create = AsyncMock(return_value=created_person)
    mock_uow.commit = AsyncMock()

    expected_response = MagicMock()
    sync_service = MagicMock()
    photo_service = _photo_service()
    with patch.object(
        PersonCreateMapper, "to_response", return_value=expected_response
    ) as mapper_mock:
        use_case = CreatePersonUseCase(
            mock_uow, photo_service, sync_service=sync_service
        )
        result = await use_case.execute(dto, tree_id=UUID(int=7))

    assert result == expected_response

    mapper_mock.assert_called_once_with(created_person, photo_url=None)
    sync_service.upsert_person.assert_called_once_with(created_person)

    assert mock_uow.persons.create.await_args is not None
    created_entity = mock_uow.persons.create.await_args.args[0]
    assert created_entity.name == "Ali"
    assert created_entity.gender == Gender.MALE
    assert created_entity.parents == []

    mock_uow.persons.get_in_tree_or_raise.assert_not_called()
    mock_uow.persons.create.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_person_with_photo(mock_uow):
    key = "persons/11111111-1111-1111-1111-111111111111.jpg"
    dto = MagicMock()
    dto.name = "Ali"
    dto.gender = Gender.MALE
    dto.birth_date = date(2000, 1, 1)
    dto.death_date = None
    dto.parents = []
    dto.marriage_id = None
    dto.photo_object_key = key

    created_person = MagicMock()
    created_person.photo_object_key = key

    mock_uow.family_trees.get_or_raise = AsyncMock()
    mock_uow.persons.create = AsyncMock(return_value=created_person)
    photo_service = _photo_service()
    photo_service.presign = AsyncMock(return_value="https://example/presigned")

    with patch.object(
        PersonCreateMapper, "to_response", return_value=MagicMock()
    ) as mapper_mock:
        use_case = CreatePersonUseCase(
            mock_uow, photo_service, sync_service=MagicMock()
        )
        await use_case.execute(dto, tree_id=UUID(int=7))

    photo_service.ensure_object_exists.assert_awaited_once_with(key)
    mapper_mock.assert_called_once_with(
        created_person, photo_url="https://example/presigned"
    )
    created_entity = mock_uow.persons.create.await_args.args[0]
    assert created_entity.photo_object_key == key
