from uuid import uuid4

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.services.person_photo_service import (
    MAX_UPLOAD_BYTES,
    PersonPhotoService,
    sniff_image_content_type,
)
from app.domain.exceptions.media_exceptions import (
    InvalidMediaContentTypeException,
    InvalidMediaObjectKeyException,
    MediaObjectNotFoundException,
    MediaTooLargeException,
)


JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 16
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
WEBP_BYTES = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 16


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

    key = await service.upload_person_photo(PNG_BYTES, "image/png")

    assert key.startswith("persons/")
    assert key.endswith(".png")
    storage.upload.assert_awaited_once()


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (JPEG_BYTES, "image/jpeg"),
        (PNG_BYTES, "image/png"),
        (WEBP_BYTES, "image/webp"),
        (b"<html>not an image</html>", None),
        (b"", None),
    ],
)
def test_sniff_image_content_type(data: bytes, expected: str | None):
    assert sniff_image_content_type(data) == expected


def test_validate_upload_bytes_accepts_matching_signature():
    service = _service()
    assert service.validate_upload_bytes(JPEG_BYTES, "image/jpeg") == "image/jpeg"


def test_validate_upload_bytes_rejects_non_image_payload():
    service = _service()
    with pytest.raises(InvalidMediaContentTypeException):
        service.validate_upload_bytes(b"GIF89a still not allowed", "image/png")


def test_validate_upload_bytes_rejects_mismatched_declaration():
    """A PNG announced as JPEG is a client lying about what it uploads."""
    service = _service()
    with pytest.raises(InvalidMediaContentTypeException):
        service.validate_upload_bytes(PNG_BYTES, "image/jpeg")


@pytest.mark.asyncio
async def test_upload_person_photo_rejects_disguised_payload():
    storage = MagicMock()
    storage.upload = AsyncMock()
    service = _service(storage)

    with pytest.raises(InvalidMediaContentTypeException):
        await service.upload_person_photo(b"#!/bin/sh\nrm -rf /", "image/png")

    storage.upload.assert_not_awaited()


def test_public_url_builds_api_path():
    service = _service()
    key = f"persons/{uuid4()}.jpg"
    assert service.public_url(key) == f"/media/{key}"
    assert service.public_url(None) is None


@pytest.mark.asyncio
async def test_get_person_photo_returns_bytes():
    storage = MagicMock()
    storage.get = AsyncMock(return_value=(JPEG_BYTES, "image/jpeg"))
    service = _service(storage)
    key = f"persons/{uuid4()}.jpg"

    body, content_type = await service.get_person_photo(key)

    assert body == JPEG_BYTES
    assert content_type == "image/jpeg"
    storage.get.assert_awaited_once_with(key)


@pytest.mark.asyncio
async def test_get_person_photo_rejects_invalid_key():
    storage = MagicMock()
    storage.get = AsyncMock()
    service = _service(storage)
    with pytest.raises(InvalidMediaObjectKeyException):
        await service.get_person_photo("../secret.jpg")
    storage.get.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_person_photo_raises_when_missing():
    storage = MagicMock()
    storage.get = AsyncMock(return_value=None)
    service = _service(storage)
    with pytest.raises(MediaObjectNotFoundException):
        await service.get_person_photo(f"persons/{uuid4()}.png")
