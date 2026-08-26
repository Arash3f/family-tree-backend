from __future__ import annotations

import hashlib
import hmac
import logging
import re
import time
from uuid import uuid4

from app.core.config import settings
from app.domain.exceptions.media_exceptions import (
    InvalidMediaContentTypeException,
    InvalidMediaObjectKeyException,
    MediaObjectNotFoundException,
    MediaTooLargeException,
)
from app.domain.repositories.object_storage import ObjectStorage

logger = logging.getLogger(__name__)

PERSON_PHOTO_PREFIX = "persons/"
ALLOWED_CONTENT_TYPES: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
# Browsers (especially mobile) often omit a real type or send a generic one.
_GENERIC_UPLOAD_TYPES = frozenset(
    {"", "application/octet-stream", "binary/octet-stream"}
)
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
_PERSON_KEY_RE = re.compile(
    rf"^{re.escape(PERSON_PHOTO_PREFIX)}"
    r"[0-9a-fA-F-]{36}\.(jpg|png|webp)$"
)


def sniff_image_content_type(data: bytes) -> str | None:
    """Identify an image from its leading bytes.

    The Content-Type header is attacker-controlled, so it only says what the
    client claims to be sending. Reading the signature is what stops an HTML or
    script payload from being stored under an image key and later served back.
    """
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _normalize_declared_type(content_type: str | None) -> str:
    return (content_type or "").split(";")[0].strip().lower()


def sign_media_access(object_key: str, expires_at: int) -> str:
    """HMAC over key + expiry so <img> can load photos without a Bearer header."""
    payload = f"{object_key}:{expires_at}".encode()
    return hmac.new(
        settings.JWT_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()


def verify_media_access(object_key: str, expires_at: int, signature: str) -> bool:
    if expires_at < int(time.time()):
        return False
    expected = sign_media_access(object_key, expires_at)
    return hmac.compare_digest(expected, signature)


class PersonPhotoService:
    """Upload validation, key rules, and photo lifecycle helpers."""

    def __init__(
        self,
        storage: ObjectStorage,
        *,
        presign_expire_seconds: int | None = None,
    ) -> None:
        self.storage = storage
        self.presign_expire_seconds = (
            settings.MINIO_PRESIGN_EXPIRE_SECONDS
            if presign_expire_seconds is None
            else presign_expire_seconds
        )

    def build_object_key(self, content_type: str) -> str:
        ext = ALLOWED_CONTENT_TYPES[content_type]
        return f"{PERSON_PHOTO_PREFIX}{uuid4()}.{ext}"

    def validate_upload(self, content_type: str | None, size: int) -> str:
        normalized = _normalize_declared_type(content_type)
        if normalized in _GENERIC_UPLOAD_TYPES:
            # Size-only check; bytes validation will sniff the real type.
            if size > MAX_UPLOAD_BYTES:
                raise MediaTooLargeException(
                    detail=[f"max size is {MAX_UPLOAD_BYTES} bytes"]
                )
            return normalized
        if normalized not in ALLOWED_CONTENT_TYPES:
            raise InvalidMediaContentTypeException(
                detail=[f"unsupported content type: {content_type!r}"]
            )
        if size > MAX_UPLOAD_BYTES:
            raise MediaTooLargeException(
                detail=[f"max size is {MAX_UPLOAD_BYTES} bytes"]
            )
        return normalized

    def validate_person_key(self, key: str) -> None:
        if not _PERSON_KEY_RE.fullmatch(key):
            raise InvalidMediaObjectKeyException(
                detail=[f"invalid photo_object_key: {key!r}"]
            )

    async def ensure_object_exists(self, key: str) -> None:
        self.validate_person_key(key)
        if not await self.storage.exists(key):
            raise MediaObjectNotFoundException(detail=[f"object not found: {key}"])

    def build_media_url(self, key: str) -> str:
        """Same-origin API path; browser reaches MinIO only through the API."""
        self.validate_person_key(key)
        expires_at = int(time.time()) + self.presign_expire_seconds
        signature = sign_media_access(key, expires_at)
        return f"/media/{key}?exp={expires_at}&sig={signature}"

    async def presign(self, key: str | None) -> str | None:
        if not key:
            return None
        return self.build_media_url(key)

    async def read_person_photo(self, key: str) -> tuple[bytes, str]:
        self.validate_person_key(key)
        result = await self.storage.get(key)
        if result is None:
            raise MediaObjectNotFoundException(detail=[f"object not found: {key}"])
        return result

    async def delete_quiet(self, key: str | None) -> None:
        if not key:
            return
        try:
            await self.storage.delete(key)
        except (OSError, RuntimeError) as e:
            logger.exception("Best-effort delete failed for key=%s: %s", key, e)

    def validate_upload_bytes(self, data: bytes, content_type: str | None) -> str:
        """Validate size and file signature; tolerate missing/generic Content-Type."""
        declared = self.validate_upload(content_type, len(data))
        detected = sniff_image_content_type(data)

        if detected is None:
            raise InvalidMediaContentTypeException(
                detail=["file content is not a supported image"]
            )
        if declared in _GENERIC_UPLOAD_TYPES:
            return detected
        if detected != declared:
            raise InvalidMediaContentTypeException(
                detail=[f"content type {declared!r} does not match file ({detected})"]
            )
        return detected

    async def upload_person_photo(self, data: bytes, content_type: str | None) -> str:
        normalized = self.validate_upload_bytes(data, content_type)
        key = self.build_object_key(normalized)
        return await self.storage.upload(data, normalized, key)
