from pydantic import Field
from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import SettingsConfigDict


class AppSettings(PydanticBaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Neo4J
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "postgres"

    # JWT:
    JWT_SECRET: str = Field(min_length=32)
    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database:
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "family_tree"
    POSTGRES_PORT: int = 5432

    # Database Test:
    POSTGRES_HOST_TEST: str = "127.0.0.1"
    POSTGRES_USER_TEST: str = "postgres"
    POSTGRES_PASSWORD_TEST: str = "postgres"
    POSTGRES_DB_TEST: str = "family_tree"
    POSTGRES_PORT_TEST: int = 5432

    # Admin User:
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"
    ADMIN_ROLE_NAME: str = "Admin"

    BACKUP_DIR: str = "/mnt/backups"

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    CORS_ORIGINS: str = (
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8001"
    )
    FLOWER_BASIC_AUTH: str = "admin:admin"
    AUTH_RATE_LIMIT_PER_MINUTE: int = 30

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


settings = AppSettings()  # type: ignore
