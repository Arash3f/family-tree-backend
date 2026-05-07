from app.application.dto.auth_dto import LoginDTO, LoginResponseDTO
from app.presentation.rest.schemas.dto.auth_schema import LoginRequest, LoginResponse


class AuthApiMapper:
    @staticmethod
    def to_login_dto(request: LoginRequest) -> LoginDTO:
        return LoginDTO(username=request.username, password=request.password)

    @staticmethod
    def from_login_dto(response: LoginResponseDTO) -> LoginResponse:
        response_data = response.model_dump()
        return LoginResponse.model_validate(response_data)
