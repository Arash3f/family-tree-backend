from pydantic import BaseModel


class LoginDTO(BaseModel):
    username: str
    password: str


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
