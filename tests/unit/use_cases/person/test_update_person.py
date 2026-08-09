from datetime import date
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.application.dto.person.person_update_dto import PersonUpdateMapper
from app.application.use_cases.person.update_person_use_case import UpdatePersonUseCase
from app.domain.entities.person import Gender


def _photo_service():
    service = MagicMock()
    service.ensure_object_exists = AsyncMock()
    service.presign = AsyncMock(return_value=None)
    service.delete_quiet = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_update_person_success(mock_uow):
    dto = MagicMock()
    dto.where.person_id = UUID(int=1)
    dto.data.model_dump.return_value = {
        "name": "Arash",
        "birth_date": date(2000, 1, 1),
    }

    person = MagicMock()
    person.safe_id = UUID(int=1)
    person.parent_ids = []
    person.parents = []
    person.marriage_id = None
    person.gender = Gender.MALE
    person.photo_object_key = None

    expected_result = MagicMock()
    sync_service = MagicMock()
    photo_service = _photo_service()

    mock_uow.persons.get_or_raise = AsyncMock(return_value=person)
    mock_uow.persons.update = AsyncMock(return_value=person)

    with patch.object(
        PersonUpdateMapper, "to_response", return_value=expected_result
    ) as mapper_mock:
        use_case = UpdatePersonUseCase(
            mock_uow, photo_service, sync_service=sync_service
        )
        result = await use_case.execute(dto)

    assert result is expected_result
    mock_uow.persons.update.assert_awaited_once_with(person=person)
    mock_uow.commit.assert_awaited_once()
    mapper_mock.assert_called_once_with(person=person, photo_url=None)
    sync_service.update_person.assert_called_once()


@pytest.mark.asyncio
async def test_update_person_replaces_photo(mock_uow):
    old_key = "persons/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa.jpg"
    new_key = "persons/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb.jpg"

    dto = MagicMock()
    dto.where.person_id = UUID(int=1)
    dto.data.model_dump.return_value = {"photo_object_key": new_key}

    person = MagicMock()
    person.safe_id = UUID(int=1)
    person.parent_ids = []
    person.parents = []
    person.marriage_id = None
    person.gender = Gender.MALE
    person.photo_object_key = old_key

    mock_uow.persons.get_or_raise = AsyncMock(return_value=person)
    mock_uow.persons.update = AsyncMock(return_value=person)

    photo_service = _photo_service()
    photo_service.presign = AsyncMock(return_value="https://example/new")

    with patch.object(PersonUpdateMapper, "to_response", return_value=MagicMock()):
        use_case = UpdatePersonUseCase(
            mock_uow, photo_service, sync_service=MagicMock()
        )
        await use_case.execute(dto)

    photo_service.ensure_object_exists.assert_awaited_once_with(new_key)
    assert person.photo_object_key == new_key
    photo_service.delete_quiet.assert_awaited_once_with(old_key)
