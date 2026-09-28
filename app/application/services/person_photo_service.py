from __future__ import annotations

import hashlib
import hmac
import io
import logging
import re
import time
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

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
# Longest edge after normalize; detail panels need more than tree avatars (~40–76px).
PERSON_PHOTO_MAX_EDGE = 1280
PERSON_PHOTO_WEBP_QUALITY = 80
STORED_CONTENT_TYPE = "image/webp"
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


def optimize_person_photo(data: bytes) -> bytes:
    """Resize (max edge) and re-encode as WebP for storage and tree bandwidth.

    Incoming bytes are already signature-validated. Pillow still has to decode
    the payload; a truncated or hostile file fails closed as invalid media.
    """
    try:
        with Image.open(io.BytesIO(data)) as image:
            image = ImageOps.exif_transpose(image)
            # Animated sources keep only the first frame for a still portrait.
            if getattr(image, "is_animated", False):
                image.seek(0)
            image = _normalize_photo_mode(image)
            image = _fit_max_edge(image, PERSON_PHOTO_MAX_EDGE)
            out = io.BytesIO()
            image.save(
                out,
                format="WEBP",
                quality=PERSON_PHOTO_WEBP_QUALITY,
                method=4,
            )
            return out.getvalue()
    except (OSError, UnidentifiedImageError, ValueError) as exc:
        raise InvalidMediaContentTypeException(
            detail=["file content is not a supported image"]
        ) from exc


def _normalize_photo_mode(image: Image.Image) -> Image.Image:
    if image.mode in {"RGB", "RGBA"}:
        return image
    if image.mode == "P":
        return image.convert("RGBA" if "transparency" in image.info else "RGB")
    if image.mode in {"LA", "PA"}:
        return image.convert("RGBA")
    return image.convert("RGB")


def _fit_max_edge(image: Image.Image, max_edge: int) -> Image.Image:
    width, height = image.size
    longest = max(width, height)
    if longest <= max_edge:
        return image
    scale = max_edge / longest
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return image.resize(size, Image.Resampling.LANCZOS)


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
        media_url_expire_seconds: int | None = None,
    ) -> None:
        self.storage = storage
        self.media_url_expire_seconds = (
            settings.MEDIA_URL_EXPIRE_SECONDS
            if media_url_expire_seconds is None
            else media_url_expire_seconds
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
        expires_at = int(time.time()) + self.media_url_expire_seconds
        signature = sign_media_access(key, expires_at)
        return f"/media/{key}?exp={expires_at}&sig={signature}"

    def media_url(self, key: str | None) -> str | None:
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
        self.validate_upload_bytes(data, content_type)
        optimized = optimize_person_photo(data)
        key = self.build_object_key(STORED_CONTENT_TYPE)
        return await self.storage.upload(optimized, STORED_CONTENT_TYPE, key)
