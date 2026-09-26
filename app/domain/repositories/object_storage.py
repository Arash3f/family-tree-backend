from abc import ABC, abstractmethod


class ObjectStorage(ABC):
    """Port for private S3-compatible object storage (e.g. MinIO).

    The browser never talks to MinIO. Callers upload/get/delete through the
    application API (signed ``/media`` URLs for reads).
    """

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
