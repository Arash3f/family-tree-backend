from uuid import UUID

from strawberry.types import Info

from app.application.dto.user.user_update_dto import (
    UserUpdateDTO,
    _UserUpdateDataDTO,
    _UserUpdateWhereDTO,
)
from app.application.use_cases.user.create_user_use_case import CreateUserUseCase
from app.application.use_cases.user.delete_user_use_case import DeleteUserUseCase
from app.application.use_cases.user.get_user_list_by_filter_use_case import (
    GetUserListByFilterUseCase,
)
from app.application.use_cases.user.get_user_use_case import GetUserUseCase
from app.application.use_cases.user.update_user_use_case import UpdateUserUseCase
from app.infrastructure.utils.constants.permissions import Permissions
from app.presentation.graphql.auth import require_permission
from app.presentation.graphql.types.common import (
    ResultType,
    pagination_dict,
    to_sort_order,
    user_sort_field,
)
from app.presentation.graphql.types.user import (
    UserCreateInput,
    UserListInput,
    UserPage,
    UserType,
    UserUpdateInput,
    user_from_mapping,
)
from app.presentation.rest.schemas.dto.common import (
    PaginationRequestParams,
    SortRequestParams,
)
from app.presentation.rest.schemas.dto.user_schema import (
    FilterUserRequest,
    UserCreateRequest,
    UserFilterRequestData,
)
from app.presentation.rest.schemas.mappers.common_mappers import CommonApiMapper
from app.presentation.rest.schemas.mappers.user_mappers import UserApiMapper


def _user_create_request(data: UserCreateInput) -> UserCreateRequest:
    return UserCreateRequest(
        username=data.username,
        password=data.password,
        re_password=data.re_password,
        role_id=data.role_id,
    )


def _user_update_dto(data: UserUpdateInput) -> UserUpdateDTO:
    raw: dict = {}
    if data.data.username is not None:
        raw["username"] = data.data.username
    if data.data.password is not None:
        raw["password"] = data.data.password
    if data.data.re_password is not None:
        raw["re_password"] = data.data.re_password
    if data.data.role_id is not None:
        raw["role_id"] = data.data.role_id
    return UserUpdateDTO(
        data=_UserUpdateDataDTO.model_construct(**raw),
        where=_UserUpdateWhereDTO(user_id=data.where.user_id),
    )


def _user_list_request(data: UserListInput | None) -> FilterUserRequest:
    payload = data or UserListInput()
    filters = None
    if payload.filters is not None:
        f = payload.filters
        filters = UserFilterRequestData(
            id=f.id, username=f.username, role_id=f.role_id
        )
    return FilterUserRequest(
        pagination=PaginationRequestParams(**pagination_dict(payload.pagination)),
        filters=filters,
        sort=SortRequestParams(
            sort_order=to_sort_order(payload.sort_order),
            sort_by=user_sort_field(payload.sort_by),
        ),
    )


async def resolve_create_user(info: Info, data: UserCreateInput) -> UserType:
    await require_permission(info, Permissions.USER_CREATE)
    usecase = CreateUserUseCase(info.context.uow, info.context.password_hasher)
    res = await usecase.execute(
        UserApiMapper.to_create_user_dto(_user_create_request(data))
    )
    mapped = UserApiMapper.from_create_user_dto(res)
    return user_from_mapping(mapped.model_dump())


async def resolve_update_user(info: Info, data: UserUpdateInput) -> UserType:
    await require_permission(info, Permissions.USER_UPDATE)
    usecase = UpdateUserUseCase(info.context.uow, info.context.password_hasher)
    res = await usecase.execute(_user_update_dto(data))
    mapped = UserApiMapper.from_update_user_dto(res)
    return user_from_mapping(mapped.model_dump())


async def resolve_delete_user(info: Info, user_id: UUID) -> ResultType:
    await require_permission(info, Permissions.USER_DELETE)
    usecase = DeleteUserUseCase(info.context.uow)
    res = await usecase.execute(CommonApiMapper.to_id_dto(user_id))
    mapped = CommonApiMapper.from_result_dto(res)
    return ResultType(result=mapped.result)


async def resolve_user(info: Info, user_id: UUID) -> UserType:
    await require_permission(info, Permissions.USER_READ)
    usecase = GetUserUseCase(info.context.uow)
    res = await usecase.execute(CommonApiMapper.to_id_dto(user_id))
    mapped = UserApiMapper.from_get_user_dto(res)
    return user_from_mapping(mapped.model_dump())


async def resolve_users(info: Info, data: UserListInput | None = None) -> UserPage:
    await require_permission(info, Permissions.USER_READ)
    usecase = GetUserListByFilterUseCase(info.context.uow)
    res = await usecase.execute(
        UserApiMapper.to_get_list_user_dto(_user_list_request(data))
    )
    mapped = UserApiMapper.from_get_list_user_dto(res)
    return UserPage(
        items=[user_from_mapping(item.model_dump()) for item in mapped.items],
        total=mapped.total,
        page=mapped.page,
        page_size=mapped.page_size,
    )
