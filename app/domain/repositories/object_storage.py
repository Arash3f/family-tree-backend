from abc import ABC, abstractmethod


class ObjectStorage(ABC):
    """Port for S3-compatible object storage (e.g. MinIO)."""

    @abstractmethod
    async def upload(self, data: bytes, content_type: str, key: str) -> str:
        """Upload object bytes and return the object key."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete an object by key. Missing keys are ignored."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Return True if the object exists."""

    @abstractmethod
    async def get(self, key: str) -> tuple[bytes, str] | None:
        """Return (body, content_type), or None if the object is missing."""

    @abstractmethod
    async def presign_get(self, key: str, expires_seconds: int) -> str:
        """Return a temporary GET URL for a private object."""
