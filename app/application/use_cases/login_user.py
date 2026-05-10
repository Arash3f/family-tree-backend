from app.application.dto.auth_dto import LoginDTO, LoginResponseDTO
from app.application.interfaces.token_service import TokenService
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.exceptions.auth_exceptions import InvalidCredentialsException
from app.domain.services.password_hasher import PasswordHasher


class LoginUserUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ):
        self.uow = uow
        self.password_hasher = password_hasher
        self.token_service = token_service

    async def execute(self, data: LoginDTO) -> LoginResponseDTO:
        async with self.uow:
            user = await self.uow.users.get_by_username(data.username)

            if not user:
                raise InvalidCredentialsException()

            if not self.password_hasher.verify(data.password, user.password_hash):
                raise InvalidCredentialsException()

            access = self.token_service.create_access_token(user.safe_id)
            refresh = self.token_service.create_refresh_token(user.safe_id)

            return LoginResponseDTO(access_token=access, refresh_token=refresh)
