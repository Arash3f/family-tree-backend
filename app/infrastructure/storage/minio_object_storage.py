from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

import aioboto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings
from app.domain.repositories.object_storage import ObjectStorage

logger = logging.getLogger(__name__)


class MinioObjectStorage(ObjectStorage):
    """Async S3-compatible client targeting MinIO."""

    def __init__(
        self,
        endpoint: str | None = None,
        public_endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        bucket: str | None = None,
        region: str | None = None,
        secure: bool | None = None,
    ) -> None:
        self._endpoint = endpoint or settings.MINIO_ENDPOINT
        self._public_endpoint = public_endpoint or settings.minio_public_endpoint
        self._access_key = access_key or settings.MINIO_ACCESS_KEY
        self._secret_key = secret_key or settings.MINIO_SECRET_KEY
        self._bucket = bucket or settings.MINIO_BUCKET
        self._region = region or settings.MINIO_REGION
        self._secure = settings.MINIO_SECURE if secure is None else secure
        self._session = aioboto3.Session()

    def _endpoint_url(self, host: str) -> str:
        scheme = "https" if self._secure else "http"
        if host.startswith("http://") or host.startswith("https://"):
            return host
        return f"{scheme}://{host}"

    def _client_kwargs(self, *, for_presign: bool = False) -> dict[str, Any]:
        host = self._public_endpoint if for_presign else self._endpoint
        return {
            "service_name": "s3",
            "endpoint_url": self._endpoint_url(host),
            "aws_access_key_id": self._access_key,
            "aws_secret_access_key": self._secret_key,
            "region_name": self._region,
            "config": Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        }

    async def ensure_buckets(self, bucket_names: list[str]) -> None:
        async with self._session.client(**self._client_kwargs()) as client:
            response = await client.list_buckets()
            existing = {bucket["Name"] for bucket in response.get("Buckets", [])}

            for name in bucket_names:
                if name in existing:
                    logger.debug("MinIO bucket already exists: %s", name)
                    continue
                await client.create_bucket(Bucket=name)
                logger.info("Created MinIO bucket: %s", name)

    async def upload(self, data: bytes, content_type: str, key: str) -> str:
        async with self._session.client(**self._client_kwargs()) as client:
            await client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
        return key

    async def delete(self, key: str) -> None:
        async with self._session.client(**self._client_kwargs()) as client:
            try:
                await client.delete_object(Bucket=self._bucket, Key=key)
            except ClientError:
                logger.exception("Failed to delete object key=%s", key)

    async def exists(self, key: str) -> bool:
        async with self._session.client(**self._client_kwargs()) as client:
            try:
                await client.head_object(Bucket=self._bucket, Key=key)
                return True
            except ClientError as exc:
                code = exc.response.get("Error", {}).get("Code")
                if code in {"404", "NoSuchKey", "NotFound"}:
                    return False
                raise

    async def get(self, key: str) -> tuple[bytes, str] | None:
        async with self._session.client(**self._client_kwargs()) as client:
            try:
                response = await client.get_object(Bucket=self._bucket, Key=key)
                body = await response["Body"].read()
                content_type = response.get("ContentType") or "application/octet-stream"
                return body, content_type
            except ClientError as exc:
                code = str(exc.response.get("Error", {}).get("Code", ""))
                if code in {"404", "NoSuchKey", "NotFound"}:
                    return None
                raise

    async def presign_get(self, key: str, expires_seconds: int) -> str:
        async with self._session.client(
            **self._client_kwargs(for_presign=True)
        ) as client:
            url = await client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=expires_seconds,
            )
        # Ensure host matches the public endpoint when path-style URLs are used.
        parsed_public = urlparse(self._endpoint_url(self._public_endpoint))
        parsed_url = urlparse(url)
        if parsed_url.hostname != parsed_public.hostname:
            url = parsed_url._replace(
                netloc=parsed_public.netloc or parsed_public.hostname or ""
            ).geturl()
        return url
