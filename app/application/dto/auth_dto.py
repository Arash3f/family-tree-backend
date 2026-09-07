from pydantic import BaseModel, Field, field_validator


class LoginDTO(BaseModel):
    username: str
    password: str


class RegisterDTO(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_.-]+$",
    )
    password: str = Field(min_length=8, max_length=256)
    re_password: str = Field(min_length=8, max_length=256)
    email: str | None = Field(
        default=None,
        max_length=255,
        pattern=r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$",
    )
    phone: str | None = Field(default=None, max_length=32)
    country_code: str | None = Field(default=None, max_length=8)

    @field_validator("email", "phone", "country_code", mode="before")
    @classmethod
    def blank_optional_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class LoginResponseDTO(BaseModel):
    access_token: str
    refresh_token: str


class LoginMapper(BaseModel):
    @staticmethod
    def to_response(access_token: str, refresh_token: str) -> LoginResponseDTO:
        return LoginResponseDTO(
            access_token=access_token,
            refresh_token=refresh_token,
        )
