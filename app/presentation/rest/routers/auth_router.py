from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.application.dto.auth_dto import LoginDTO
from app.application.use_cases.login_user import LoginUserUseCase
from app.application.use_cases.logout_user import LogoutAllUseCase, LogoutUseCase
from app.application.use_cases.refresh_token import RefreshTokenUseCase
from app.domain.entities.user import User
from app.presentation.rest.dependencies.auth_dependencies import (
    get_current_session_id,
    get_current_user,
)
from app.presentation.rest.dependencies.rate_limit import rate_limit_auth
from app.presentation.rest.schemas.dto.auth_schema import LoginResponse
from app.presentation.rest.schemas.dto.common import ResultResponse
from app.presentation.rest.schemas.dto.user_schema import UserGetResponse
from app.presentation.rest.schemas.mappers.auth_mappers import AuthApiMapper
from app.presentation.rest.schemas.mappers.common_mappers import CommonApiMapper
from app.presentation.rest.utils.dependencies import (
    get_password_hasher,
    get_token_service,
    get_uow,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


class RefreshTokenRequest(BaseModel):
    refresh_token: str


def _client_meta(request: Request) -> tuple[str | None, str | None]:
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    return user_agent, ip_address


@router.post(
    "/login",
    response_model=LoginResponse,
    dependencies=[Depends(rate_limit_auth)],
)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    uow=Depends(get_uow),
    token_service=Depends(get_token_service),
    password_hasher=Depends(get_password_hasher),
) -> LoginResponse:
    data = LoginDTO(
        password=form_data.password,
        username=form_data.username,
    )
    user_agent, ip_address = _client_meta(request)
    usecase = LoginUserUseCase(uow, password_hasher, token_service)

    tokens = await usecase.execute(
        data, user_agent=user_agent, ip_address=ip_address
    )

    return AuthApiMapper.from_login_dto(tokens)


@router.post(
    "/refresh",
    response_model=LoginResponse,
    dependencies=[Depends(rate_limit_auth)],
)
async def refresh(
    request: Request,
    data: RefreshTokenRequest,
    uow=Depends(get_uow),
    token_service=Depends(get_token_service),
) -> LoginResponse:
    user_agent, ip_address = _client_meta(request)
    usecase = RefreshTokenUseCase(uow, token_service)
    tokens = await usecase.execute(
        data.refresh_token, user_agent=user_agent, ip_address=ip_address
    )
    return AuthApiMapper.from_login_dto(tokens)


@router.post("/logout", response_model=ResultResponse)
async def logout(
    current_user: User = Depends(get_current_user),
    session_id=Depends(get_current_session_id),
    uow=Depends(get_uow),
) -> ResultResponse:
    usecase = LogoutUseCase(uow)
    result = await usecase.execute(session_id=session_id, user_id=current_user.safe_id)
    return CommonApiMapper.from_result_dto(result)


@router.post("/logout-all", response_model=ResultResponse)
async def logout_all(
    current_user: User = Depends(get_current_user),
    uow=Depends(get_uow),
) -> ResultResponse:
    usecase = LogoutAllUseCase(uow)
    result = await usecase.execute(user_id=current_user.safe_id)
    return CommonApiMapper.from_result_dto(result)


@router.get("/me", response_model=UserGetResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserGetResponse:
    return UserGetResponse(
        id=current_user.safe_id,
        username=current_user.username,
        role_id=current_user.role_id,
    )
