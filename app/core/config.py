from pydantic_settings import BaseSettings as PydanticBaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(PydanticBaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    POSTGRES_HOST: str = Field(...)
    POSTGRES_USER: str = Field(...)
    POSTGRES_PASSWORD: str = Field(...)
    POSTGRES_DB: str = Field(...)
    POSTGRES_PORT: int = Field(...)

    @property
    def database_url_asy(self):
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def database_url(self):
        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


setting = Settings()
