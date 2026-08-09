from uuid import uuid4

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.services.person_photo_service import (
    MAX_UPLOAD_BYTES,
    PersonPhotoService,
)
from app.domain.exceptions.media_exceptions import (
    InvalidMediaContentTypeException,
    InvalidMediaObjectKeyException,
    MediaObjectNotFoundException,
    MediaTooLargeException,
)


def _service(storage: MagicMock | None = None) -> PersonPhotoService:
    return PersonPhotoService(storage or MagicMock(), presign_expire_seconds=60)


def test_validate_upload_accepts_jpeg():
    service = _service()
    assert service.validate_upload("image/jpeg", 100) == "image/jpeg"


def test_validate_upload_rejects_type():
    service = _service()
    with pytest.raises(InvalidMediaContentTypeException):
        service.validate_upload("application/pdf", 100)


def test_validate_upload_rejects_size():
    service = _service()
    with pytest.raises(MediaTooLargeException):
        service.validate_upload("image/png", MAX_UPLOAD_BYTES + 1)


def test_build_object_key_uses_persons_prefix():
    service = _service()
    key = service.build_object_key("image/webp")
    assert key.startswith("persons/")
    assert key.endswith(".webp")


def test_validate_person_key_ok():
    service = _service()
    key = f"persons/{uuid4()}.jpg"
    service.validate_person_key(key)


def test_validate_person_key_rejects_path_traversal():
    service = _service()
    with pytest.raises(InvalidMediaObjectKeyException):
        service.validate_person_key("../secret.jpg")


@pytest.mark.asyncio
async def test_ensure_object_exists_raises_when_missing():
    storage = MagicMock()
    storage.exists = AsyncMock(return_value=False)
    service = _service(storage)
    with pytest.raises(MediaObjectNotFoundException):
        await service.ensure_object_exists(f"persons/{uuid4()}.png")


@pytest.mark.asyncio
async def test_upload_person_photo():
    storage = MagicMock()
    storage.upload = AsyncMock(side_effect=lambda data, content_type, key: key)
    service = _service(storage)

    key = await service.upload_person_photo(b"abc", "image/png")

    assert key.startswith("persons/")
    assert key.endswith(".png")
    storage.upload.assert_awaited_once()
