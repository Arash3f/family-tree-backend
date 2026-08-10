from uuid import UUID

from fastapi import APIRouter, Depends

from app.application.use_cases.session.session_use_cases import (
    ListUserSessionsUseCase,
    RevokeAllUserSessionsUseCase,
    RevokeUserSessionUseCase,
)
from app.application.use_cases.user.create_user_use_case import CreateUserUseCase
from app.application.use_cases.user.delete_user_use_case import DeleteUserUseCase
from app.application.use_cases.user.get_user_list_by_filter_use_case import (
    GetUserListByFilterUseCase,
)
from app.application.use_cases.user.get_user_use_case import GetUserUseCase
from app.application.use_cases.user.update_user_use_case import UpdateUserUseCase
from app.domain.entities.user import User
from app.domain.services.password_hasher import PasswordHasher
from app.domain.shared.permissions import Permissions
from app.presentation.rest.dependencies.auth_dependencies import get_current_session_id
from app.presentation.rest.dependencies.permission_guard import RequirePermission
from app.presentation.rest.schemas.dto.auth_schema import SessionResponse
from app.presentation.rest.schemas.dto.common import PaginatedResponse, ResultResponse
from app.presentation.rest.schemas.dto.user_schema import (
    FilterUserRequest,
    UserCreateRequest,
    UserCreateResponse,
    UserGetResponse,
    UserModel,
    UserUpdateRequest,
    UserUpdateResponse,
)
from app.presentation.rest.schemas.mappers.common_mappers import CommonApiMapper
from app.presentation.rest.schemas.mappers.user_mappers import UserApiMapper
from app.presentation.rest.utils.dependencies import get_password_hasher, get_uow

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/",
    response_model=UserCreateResponse,
    dependencies=[Depends(RequirePermission(Permissions.USER_CREATE))],
)
async def create_user(
    data: UserCreateRequest,
    uow=Depends(get_uow),
    hasher: PasswordHasher = Depends(get_password_hasher),
) -> UserCreateResponse:
    usecase = CreateUserUseCase(uow, hasher)

    res = await usecase.execute(UserApiMapper.to_create_user_dto(data))

    return UserApiMapper.from_create_user_dto(res)


@router.delete(
    "/{user_id}",
    response_model=ResultResponse,
    dependencies=[Depends(RequirePermission(Permissions.USER_DELETE))],
)
async def delete_user(
    user_id: UUID,
    uow=Depends(get_uow),
) -> ResultResponse:
    usecase = DeleteUserUseCase(uow)

    res = await usecase.execute(CommonApiMapper.to_id_dto(user_id))

    return CommonApiMapper.from_result_dto(res)


@router.put(
    "/",
    response_model=UserUpdateResponse,
)
async def update_user(
    data: UserUpdateRequest,
    current_user: User = Depends(RequirePermission(Permissions.USER_UPDATE)),
    uow=Depends(get_uow),
    hasher: PasswordHasher = Depends(get_password_hasher),
) -> UserUpdateResponse:
    usecase = UpdateUserUseCase(uow, hasher, current_user=current_user)

    res = await usecase.execute(UserApiMapper.to_update_user_dto(data))

    return UserApiMapper.from_update_user_dto(res)


@router.get(
    "/{user_id}",
    response_model=UserGetResponse,
    dependencies=[Depends(RequirePermission(Permissions.USER_READ))],
)
async def get_user(
    user_id: UUID,
    uow=Depends(get_uow),
) -> UserGetResponse:
    usecase = GetUserUseCase(uow)

    res = await usecase.execute(CommonApiMapper.to_id_dto(user_id))

    return UserApiMapper.from_get_user_dto(res)


@router.post(
    "/list",
    response_model=PaginatedResponse[UserModel],
    dependencies=[Depends(RequirePermission(Permissions.USER_READ))],
)
async def get_user_list_by_filter(
    data: FilterUserRequest,
    uow=Depends(get_uow),
) -> PaginatedResponse[UserModel]:
    usecase = GetUserListByFilterUseCase(uow)

    res = await usecase.execute(UserApiMapper.to_get_list_user_dto(data))

    return UserApiMapper.from_get_list_user_dto(res)


@router.get(
    "/{user_id}/sessions",
    response_model=list[SessionResponse],
    dependencies=[Depends(RequirePermission(Permissions.USER_UPDATE))],
)
async def list_user_sessions(
    user_id: UUID,
    current_session_id: UUID = Depends(get_current_session_id),
    uow=Depends(get_uow),
) -> list[SessionResponse]:
    usecase = ListUserSessionsUseCase(uow)
    items = await usecase.execute(user_id, current_session_id=current_session_id)
    return [
        SessionResponse(
            id=item.id,
            user_agent=item.user_agent,
            ip_address=item.ip_address,
            created_at=item.created_at,
            expires_at=item.expires_at,
            is_current=item.is_current,
        )
        for item in items
    ]


@router.delete(
    "/{user_id}/sessions/{session_id}",
    response_model=ResultResponse,
    dependencies=[Depends(RequirePermission(Permissions.USER_UPDATE))],
)
async def revoke_user_session(
    user_id: UUID,
    session_id: UUID,
    uow=Depends(get_uow),
) -> ResultResponse:
    usecase = RevokeUserSessionUseCase(uow)
    result = await usecase.execute(user_id=user_id, session_id=session_id)
    return CommonApiMapper.from_result_dto(result)


@router.post(
    "/{user_id}/sessions/revoke-all",
    response_model=ResultResponse,
    dependencies=[Depends(RequirePermission(Permissions.USER_UPDATE))],
)
async def revoke_all_user_sessions(
    user_id: UUID,
    uow=Depends(get_uow),
) -> ResultResponse:
    usecase = RevokeAllUserSessionsUseCase(uow)
    result = await usecase.execute(user_id)
    return CommonApiMapper.from_result_dto(result)
