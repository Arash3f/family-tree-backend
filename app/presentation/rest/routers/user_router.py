from fastapi import APIRouter, Depends

from app.application.use_cases.user.create_user_use_case import CreateUserUseCase
from app.application.use_cases.user.delete_user_use_case import DeleteUserUseCase
from app.application.use_cases.user.get_user_list_by_filter_use_case import (
    GetUserListByFilterUseCase,
)
from app.application.use_cases.user.get_user_use_case import GetUserUseCase
from app.application.use_cases.user.update_user_use_case import UpdateUserUseCase
from app.domain.services.password_hasher import PasswordHasher
from app.infrastructure.utils.constants.permissions import Permissions
from app.presentation.rest.dependencies.permission_guard import RequirePermission
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
from app.presentation.rest.schemas.mappers.comman_mappers import CommonApiMapper
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
    user_id: int,
    uow=Depends(get_uow),
) -> ResultResponse:
    usecase = DeleteUserUseCase(uow)

    res = await usecase.execute(CommonApiMapper.to_id_dto(user_id))

    return CommonApiMapper.from_result_dto(res)


@router.put(
    "/",
    response_model=UserUpdateResponse,
    dependencies=[Depends(RequirePermission(Permissions.USER_UPDATE))],
)
async def update_user(
    data: UserUpdateRequest,
    uow=Depends(get_uow),
    hasher: PasswordHasher = Depends(get_password_hasher),
) -> UserUpdateResponse:
    usecase = UpdateUserUseCase(uow, hasher)

    res = await usecase.execute(UserApiMapper.to_update_user_dto(data))

    return UserApiMapper.from_update_user_dto(res)


@router.get(
    "/{user_id}",
    response_model=UserGetResponse,
    dependencies=[Depends(RequirePermission(Permissions.USER_READ))],
)
async def get_user(
    user_id: int,
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
