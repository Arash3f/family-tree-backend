from pydantic_settings import BaseSettings as PydanticBaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(PydanticBaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # JWT:
    JWT_SECRET: str = Field(...)
    JWT_ALGORITHM: str = Field(...)

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(...)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(...)

    # Database:
    POSTGRES_HOST: str = Field(...)
    POSTGRES_USER: str = Field(...)
    POSTGRES_PASSWORD: str = Field(...)
    POSTGRES_DB: str = Field(...)
    POSTGRES_PORT: int = Field(...)

    # Database Test:
    POSTGRES_HOST_TEST: str = Field(...)
    POSTGRES_USER_TEST: str = Field(...)
    POSTGRES_PASSWORD_TEST: str = Field(...)
    POSTGRES_DB_TEST: str = Field(...)
    POSTGRES_PORT_TEST: int = Field(...)

    # Admin User:
    ADMIN_USERNAME: str = Field(...)
    ADMIN_PASSWORD: str = Field(...)
    ADMIN_ROLE_NAME: str = Field(...)

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
