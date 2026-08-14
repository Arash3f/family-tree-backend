from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.use_cases.media.get_media_use_case import GetMediaUseCase


@pytest.mark.asyncio
async def test_get_media_use_case():
    photo_service = MagicMock()
    photo_service.get_person_photo = AsyncMock(
        return_value=(b"\xff\xd8\xff", "image/jpeg")
    )

    usecase = GetMediaUseCase(photo_service)
    body, content_type = await usecase.execute(
        "persons/11111111-1111-1111-1111-111111111111.jpg"
    )

    assert body.startswith(b"\xff\xd8")
    assert content_type == "image/jpeg"
    photo_service.get_person_photo.assert_awaited_once()
