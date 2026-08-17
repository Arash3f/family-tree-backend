from strawberry.types import Info

from app.application.dto.auth_dto import LoginDTO
from app.application.use_cases.login_user import LoginUserUseCase
from app.application.use_cases.logout_user import LogoutAllUseCase, LogoutUseCase
from app.application.use_cases.refresh_token import RefreshTokenUseCase
from app.presentation.graphql.auth import (
    client_meta,
    enforce_auth_rate_limit,
    get_current_session_id,
    get_current_user,
)
from app.presentation.graphql.types.common import ResultType
from app.presentation.graphql.types.user import (
    AuthTokensType,
    UserType,
    user_from_mapping,
)
from app.presentation.rest.schemas.mappers.auth_mappers import AuthApiMapper
from app.presentation.rest.schemas.mappers.common_mappers import CommonApiMapper


async def resolve_login(
    info: Info,
    username: str,
    password: str,
) -> AuthTokensType:
    await enforce_auth_rate_limit(info)
    ctx = info.context
    user_agent, ip_address = client_meta(info)
    usecase = LoginUserUseCase(ctx.uow, ctx.password_hasher, ctx.token_service)
    tokens = await usecase.execute(
        LoginDTO(username=username, password=password),
        user_agent=user_agent,
        ip_address=ip_address,
    )
    mapped = AuthApiMapper.from_login_dto(tokens)
    return AuthTokensType(
        access_token=mapped.access_token,
        refresh_token=mapped.refresh_token,
        token_type=mapped.token_type,
    )


async def resolve_refresh_token(info: Info, refresh_token: str) -> AuthTokensType:
    await enforce_auth_rate_limit(info)
    ctx = info.context
    user_agent, ip_address = client_meta(info)
    usecase = RefreshTokenUseCase(ctx.uow, ctx.token_service)
    tokens = await usecase.execute(
        refresh_token, user_agent=user_agent, ip_address=ip_address
    )
    mapped = AuthApiMapper.from_login_dto(tokens)
    return AuthTokensType(
        access_token=mapped.access_token,
        refresh_token=mapped.refresh_token,
        token_type=mapped.token_type,
    )


async def resolve_logout(info: Info) -> ResultType:
    user = await get_current_user(info)
    session_id = get_current_session_id(user)
    usecase = LogoutUseCase(info.context.uow)
    result = await usecase.execute(session_id=session_id, user_id=user.safe_id)
    mapped = CommonApiMapper.from_result_dto(result)
    return ResultType(result=mapped.result)


async def resolve_logout_all(info: Info) -> ResultType:
    user = await get_current_user(info)
    usecase = LogoutAllUseCase(info.context.uow)
    result = await usecase.execute(user_id=user.safe_id)
    mapped = CommonApiMapper.from_result_dto(result)
    return ResultType(result=mapped.result)


async def resolve_me(info: Info) -> UserType:
    user = await get_current_user(info)
    return user_from_mapping(
        {
            "id": user.safe_id,
            "username": user.username,
            "fullname": user.fullname,
            "role_id": user.role_id,
            "account_type": user.account_type.value,
        }
    )
