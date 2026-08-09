from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import UploadFile

from app.application.use_cases.media.upload_media_use_case import UploadMediaUseCase


@pytest.mark.asyncio
async def test_upload_media_use_case():
    photo_service = MagicMock()
    photo_service.upload_person_photo = AsyncMock(
        return_value="persons/11111111-1111-1111-1111-111111111111.jpg"
    )

    file = MagicMock(spec=UploadFile)
    file.content_type = "image/jpeg"
    file.read = AsyncMock(return_value=b"jpeg-bytes")

    usecase = UploadMediaUseCase(photo_service)
    result = await usecase.execute(file)

    assert result.object_key.endswith(".jpg")
    photo_service.upload_person_photo.assert_awaited_once_with(
        b"jpeg-bytes", "image/jpeg"
    )
