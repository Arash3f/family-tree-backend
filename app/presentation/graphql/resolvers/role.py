from uuid import UUID

from strawberry.types import Info

from app.application.dto.role.role_update_dto import (
    RoleUpdateDTO,
    _RoleUpdateDataDTO,
    _RoleUpdateWhereDTO,
)
from app.application.use_cases.role.create_role_use_case import CreateRoleUseCase
from app.application.use_cases.role.delete_role_use_case import DeleteRoleUseCase
from app.application.use_cases.role.get_role_list_by_filter_use_case import (
    GetRoleListByFilterUseCase,
)
from app.application.use_cases.role.get_role_use_case import GetRoleUseCase
from app.application.use_cases.role.update_role_use_case import UpdateRoleUseCase
from app.infrastructure.utils.constants.permissions import Permissions
from app.presentation.graphql.auth import require_permission
from app.presentation.graphql.types.common import (
    ResultType,
    pagination_dict,
    role_sort_field,
    to_sort_order,
)
from app.presentation.graphql.types.role import (
    RoleCreateInput,
    RoleListInput,
    RolePage,
    RoleType,
    RoleUpdateInput,
    role_from_mapping,
)
from app.presentation.rest.schemas.dto.common import (
    PaginationRequestParams,
    SortRequestParams,
)
from app.presentation.rest.schemas.dto.role_schema import (
    FilterRoleRequest,
    RoleCreateRequest,
    RoleFilterRequestData,
)
from app.presentation.rest.schemas.mappers.common_mappers import CommonApiMapper
from app.presentation.rest.schemas.mappers.role_mappers import RoleApiMapper


def _role_create_request(data: RoleCreateInput) -> RoleCreateRequest:
    return RoleCreateRequest(name=data.name, permission_ids=data.permission_ids)


def _role_update_dto(data: RoleUpdateInput) -> RoleUpdateDTO:
    raw: dict = {}
    if data.data.name is not None:
        raw["name"] = data.data.name
    if data.data.permission_ids is not None:
        raw["permission_ids"] = data.data.permission_ids
    return RoleUpdateDTO(
        data=_RoleUpdateDataDTO.model_construct(**raw),
        where=_RoleUpdateWhereDTO(role_id=data.where.role_id),
    )


def _role_list_request(data: RoleListInput | None) -> FilterRoleRequest:
    payload = data or RoleListInput()
    filters = None
    if payload.filters is not None:
        f = payload.filters
        filters = RoleFilterRequestData(
            id=f.id, name=f.name, permission_id=f.permission_id
        )
    return FilterRoleRequest(
        pagination=PaginationRequestParams(**pagination_dict(payload.pagination)),
        filters=filters,
        sort=SortRequestParams(
            sort_order=to_sort_order(payload.sort_order),
            sort_by=role_sort_field(payload.sort_by),
        ),
    )


async def resolve_create_role(info: Info, data: RoleCreateInput) -> RoleType:
    await require_permission(info, Permissions.ROLE_CREATE)
    usecase = CreateRoleUseCase(info.context.uow)
    res = await usecase.execute(
        RoleApiMapper.to_create_role_dto(_role_create_request(data))
    )
    mapped = RoleApiMapper.from_create_role_dto(res)
    return role_from_mapping(mapped.model_dump())


async def resolve_update_role(info: Info, data: RoleUpdateInput) -> RoleType:
    await require_permission(info, Permissions.ROLE_UPDATE)
    usecase = UpdateRoleUseCase(info.context.uow)
    res = await usecase.execute(_role_update_dto(data))
    mapped = RoleApiMapper.from_update_role_dto(res)
    return role_from_mapping(mapped.model_dump())


async def resolve_delete_role(info: Info, role_id: UUID) -> ResultType:
    await require_permission(info, Permissions.ROLE_DELETE)
    usecase = DeleteRoleUseCase(info.context.uow)
    res = await usecase.execute(CommonApiMapper.to_id_dto(role_id))
    mapped = CommonApiMapper.from_result_dto(res)
    return ResultType(result=mapped.result)


async def resolve_role(info: Info, role_id: UUID) -> RoleType:
    await require_permission(info, Permissions.ROLE_READ)
    usecase = GetRoleUseCase(info.context.uow)
    res = await usecase.execute(CommonApiMapper.to_id_dto(role_id))
    mapped = RoleApiMapper.from_get_role_dto(res)
    return role_from_mapping(mapped.model_dump())


async def resolve_roles(info: Info, data: RoleListInput | None = None) -> RolePage:
    await require_permission(info, Permissions.ROLE_READ)
    usecase = GetRoleListByFilterUseCase(info.context.uow)
    res = await usecase.execute(
        RoleApiMapper.to_get_list_role_dto(_role_list_request(data))
    )
    mapped = RoleApiMapper.from_get_list_role_dto(res)
    return RolePage(
        items=[role_from_mapping(item.model_dump()) for item in mapped.items],
        total=mapped.total,
        page=mapped.page,
        page_size=mapped.page_size,
    )
