from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import SettingsConfigDict


class AppSettings(PydanticBaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # local | development | staging | production
    ENVIRONMENT: str = "local"

    # Neo4J
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "postgres"

    # JWT:
    JWT_SECRET: str = Field(min_length=32)
    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60

    # Database:
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "family_tree"
    POSTGRES_PORT: int = 5432

    # Async engine connection pool. Explicit values instead of SQLAlchemy's
    # defaults so pool exhaustion under load is a deliberate, tunable limit
    # rather than whatever the library happens to default to.
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT_SECONDS: int = 30
    DB_POOL_RECYCLE_SECONDS: int = 1800

    # Database Test (must be a separate database — e2e drops/recreates schema):
    POSTGRES_HOST_TEST: str = "127.0.0.1"
    POSTGRES_USER_TEST: str = "postgres"
    POSTGRES_PASSWORD_TEST: str = "postgres"
    POSTGRES_DB_TEST: str = "family_tree_test"
    POSTGRES_PORT_TEST: int = 5432

    # Admin User:
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"
    ADMIN_ROLE_NAME: str = "Admin"

    BACKUP_DIR: str = "/mnt/backups"

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    CORS_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:8001,http://localhost,http://127.0.0.1,"
        "http://localhost:80,http://127.0.0.1:80"
    )
    AUTH_RATE_LIMIT_PER_MINUTE: int = 30

    # GraphQL hardening. A single query can fan out far more work than a REST
    # call, so cap how large an incoming document may be.
    GRAPHQL_MAX_DEPTH: int = 10
    GRAPHQL_MAX_ALIASES: int = 15
    GRAPHQL_MAX_TOKENS: int = 2000

    # MinIO / S3-compatible object storage
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_PUBLIC_ENDPOINT: str | None = None
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "family-tree"
    # Comma-separated bucket names ensured on startup. Defaults to MINIO_BUCKET.
    MINIO_BUCKETS: str | None = None
    MINIO_REGION: str = "us-east-1"
    MINIO_SECURE: bool = False
    MINIO_PRESIGN_EXPIRE_SECONDS: int = 3600

    @model_validator(mode="after")
    def ensure_test_database_is_separate(self) -> Self:
        same_target = (
            self.POSTGRES_HOST == self.POSTGRES_HOST_TEST
            and self.POSTGRES_PORT == self.POSTGRES_PORT_TEST
            and self.POSTGRES_DB == self.POSTGRES_DB_TEST
        )
        if same_target:
            raise ValueError(
                "POSTGRES_DB_TEST must target a different database than POSTGRES_DB "
                "(same host/port/name would let tests wipe app data). "
                f"Got {self.POSTGRES_DB!r} on "
                f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}."
            )
        return self

    @property
    def normalized_environment(self) -> str:
        return (self.ENVIRONMENT or "local").strip().lower()

    @property
    def is_development_like(self) -> bool:
        """Whether developer conveniences (GraphiQL, introspection) are safe here."""
        return self.normalized_environment in {"local", "development", "dev", "test"}

    @model_validator(mode="after")
    def reject_weak_secrets_outside_local(self) -> Self:
        """Allow weak demo defaults only in local/development."""
        env = self.normalized_environment
        if self.is_development_like:
            return self

        weak: list[str] = []
        if self.ADMIN_PASSWORD in {"admin", "password", "123456"}:
            weak.append("ADMIN_PASSWORD")
        if self.NEO4J_PASSWORD in {"postgres", "neo4j", "password"}:
            weak.append("NEO4J_PASSWORD")
        if self.POSTGRES_PASSWORD in {"postgres", "password"}:
            weak.append("POSTGRES_PASSWORD")
        if (
            self.MINIO_ACCESS_KEY == "minioadmin"  # pragma: allowlist secret
            or self.MINIO_SECRET_KEY == "minioadmin"  # pragma: allowlist secret
        ):
            weak.append("MINIO_ACCESS_KEY/MINIO_SECRET_KEY")
        if self.JWT_SECRET.startswith("local-dev-only"):  # pragma: allowlist secret
            weak.append("JWT_SECRET")
        if "*" in {origin.strip() for origin in self.CORS_ORIGINS.split(",")}:
            weak.append("CORS_ORIGINS")

        if weak:
            raise ValueError(
                "Weak/default secrets are not allowed when "
                f"ENVIRONMENT={env!r}. Change: {', '.join(weak)}."
            )
        return self

    @property
    def database_url_asy(self):
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def database_test_asy(self):
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER_TEST}:"
            f"{self.POSTGRES_PASSWORD_TEST}@{self.POSTGRES_HOST_TEST}:"
            f"{self.POSTGRES_PORT_TEST}/{self.POSTGRES_DB_TEST}"
        )

    @property
    def database_url(self):
        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def minio_public_endpoint(self) -> str:
        return self.MINIO_PUBLIC_ENDPOINT or self.MINIO_ENDPOINT

    @property
    def minio_buckets(self) -> list[str]:
        source = (
            self.MINIO_BUCKETS if self.MINIO_BUCKETS is not None else self.MINIO_BUCKET
        )
        buckets = [name.strip() for name in source.split(",") if name.strip()]
        if not buckets:
            raise ValueError(
                "At least one MinIO bucket name is required (MINIO_BUCKETS)."
            )
        return buckets

    @model_validator(mode="after")
    def ensure_minio_bucket_is_listed(self) -> Self:
        if self.MINIO_BUCKET not in self.minio_buckets:
            raise ValueError(
                f"MINIO_BUCKET {self.MINIO_BUCKET!r} must appear in MINIO_BUCKETS."
            )
        return self


settings = AppSettings()  # type: ignore
