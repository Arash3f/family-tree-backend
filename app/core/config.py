from pydantic_settings import BaseSettings as PydanticBaseSettings, SettingsConfigDict


class Settings(PydanticBaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # JWT:
    JWT_SECRET: str = "wzexsdcfvghjkml"
    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 60

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
    POSTGRES_DB_TEST: str = "family_tree_test"
    POSTGRES_PORT_TEST: int = 5432

    # Admin User:
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"
    ADMIN_ROLE_NAME: str = "admin"

    BACKUP_DIR: str = "/backups"

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

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


setting = Settings()  # type: ignore
