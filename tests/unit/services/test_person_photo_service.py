from io import BytesIO
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from PIL import Image

from app.application.services.person_photo_service import (
    MAX_UPLOAD_BYTES,
    PERSON_PHOTO_MAX_EDGE,
    PersonPhotoService,
    optimize_person_photo,
    sniff_image_content_type,
)
from app.domain.exceptions.media_exceptions import (
    InvalidMediaContentTypeException,
    InvalidMediaObjectKeyException,
    MediaObjectNotFoundException,
    MediaTooLargeException,
)


def _png_bytes(*, size: tuple[int, int] = (32, 24), color=(20, 40, 60)) -> bytes:
    image = Image.new("RGB", size, color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _jpeg_bytes(*, size: tuple[int, int] = (32, 24)) -> bytes:
    image = Image.new("RGB", size, (200, 100, 50))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def _webp_bytes(*, size: tuple[int, int] = (32, 24)) -> bytes:
    image = Image.new("RGB", size, (10, 120, 80))
    buffer = BytesIO()
    image.save(buffer, format="WEBP", quality=90)
    return buffer.getvalue()


JPEG_BYTES = _jpeg_bytes()
PNG_BYTES = _png_bytes()
WEBP_BYTES = _webp_bytes()


def _service(storage: MagicMock | None = None) -> PersonPhotoService:
    return PersonPhotoService(storage or MagicMock(), media_url_expire_seconds=60)


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
async def test_upload_person_photo_stores_optimized_webp():
    storage = MagicMock()
    storage.upload = AsyncMock(side_effect=lambda data, content_type, key: key)
    service = _service(storage)

    key = await service.upload_person_photo(PNG_BYTES, "image/png")

    assert key.startswith("persons/")
    assert key.endswith(".webp")
    storage.upload.assert_awaited_once()
    uploaded_data, uploaded_type, _uploaded_key = storage.upload.await_args.args
    assert uploaded_type == "image/webp"
    assert sniff_image_content_type(uploaded_data) == "image/webp"
    with Image.open(BytesIO(uploaded_data)) as image:
        assert image.format == "WEBP"
        assert max(image.size) <= PERSON_PHOTO_MAX_EDGE


def test_optimize_person_photo_downscales_long_edge():
    source = _png_bytes(size=(2400, 1600))
    optimized = optimize_person_photo(source)
    with Image.open(BytesIO(optimized)) as image:
        assert image.size == (PERSON_PHOTO_MAX_EDGE, 853)


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


def test_validate_upload_bytes_sniffs_when_type_missing():
    service = _service()
    assert service.validate_upload_bytes(PNG_BYTES, None) == "image/png"
    assert service.validate_upload_bytes(JPEG_BYTES, "") == "image/jpeg"
    assert (
        service.validate_upload_bytes(WEBP_BYTES, "application/octet-stream")
        == "image/webp"
    )


@pytest.mark.asyncio
async def test_upload_person_photo_rejects_disguised_payload():
    storage = MagicMock()
    storage.upload = AsyncMock()
    service = _service(storage)

    with pytest.raises(InvalidMediaContentTypeException):
        await service.upload_person_photo(b"#!/bin/sh\nrm -rf /", "image/png")

    storage.upload.assert_not_awaited()


def test_media_url_returns_none_for_missing_key():
    service = _service()
    assert service.media_url(None) is None


def test_media_url_returns_signed_api_path():
    service = _service()
    key = f"persons/{uuid4()}.jpg"

    url = service.media_url(key)

    assert url is not None
    assert url.startswith(f"/media/{key}?exp=")
    assert "&sig=" in url
