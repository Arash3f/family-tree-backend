from fastapi import APIRouter, Depends

from app.application.use_cases.role.create_role_use_case import CreateRoleUseCase
from app.application.use_cases.role.delete_role_use_case import DeleteRoleUseCase
from app.application.use_cases.role.get_role_list_by_filter_use_case import (
    GetRoleListByFilterUseCase,
)
from app.application.use_cases.role.get_role_use_case import GetRoleUseCase
from app.application.use_cases.role.update_role_use_case import UpdateRoleUseCase
from app.domain.constants.permissions import Permissions
from app.presentation.rest.utils.dependencies import get_uow
from app.presentation.rest.schemas.dto.common import PaginatedResponse, ResultResponse

from app.presentation.rest.schemas.dto.role_schema import (
    FilterRoleRequest,
    RoleCreateRequest,
    RoleCreateResponse,
    RoleGetResponse,
    RoleModel,
    RoleUpdateRequest,
    RoleUpdateResponse,
)
from app.presentation.rest.schemas.mappers.comman_mappers import CommonApiMapper
from app.presentation.rest.schemas.mappers.role_mappers import RoleApiMapper
from app.presentation.rest.dependencies.permission_guard import RequirePermission

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.post(
    "/",
    response_model=RoleCreateResponse,
    dependencies=[Depends(RequirePermission(Permissions.ROLE_CREATE))],
)
async def create_role(
    data: RoleCreateRequest,
    uow=Depends(get_uow),
) -> RoleCreateResponse:
    usecase = CreateRoleUseCase(uow)

    res = await usecase.execute(RoleApiMapper.to_create_role_dto(data))

    return RoleApiMapper.from_create_role_dto(res)


@router.delete(
    "/{role_id}",
    response_model=ResultResponse,
    dependencies=[Depends(RequirePermission(Permissions.ROLE_DELETE))],
)
async def delete_role(
    role_id: int,
    uow=Depends(get_uow),
) -> ResultResponse:
    usecase = DeleteRoleUseCase(uow)

    res = await usecase.execute(CommonApiMapper.to_id_dto(role_id))

    return CommonApiMapper.from_result_dto(res)


@router.put(
    "/",
    response_model=RoleUpdateResponse,
    dependencies=[Depends(RequirePermission(Permissions.ROLE_UPDATE))],
)
async def update_role(
    data: RoleUpdateRequest,
    uow=Depends(get_uow),
) -> RoleUpdateResponse:
    usecase = UpdateRoleUseCase(uow)

    res = await usecase.execute(RoleApiMapper.to_update_role_dto(data))

    return RoleApiMapper.from_update_role_dto(res)


@router.get(
    "/{role_id}",
    response_model=RoleGetResponse,
    dependencies=[Depends(RequirePermission(Permissions.ROLE_READ))],
)
async def get_role(
    role_id: int,
    uow=Depends(get_uow),
) -> RoleGetResponse:
    usecase = GetRoleUseCase(uow)

    res = await usecase.execute(CommonApiMapper.to_id_dto(role_id))

    return RoleApiMapper.from_get_role_dto(res)


@router.post(
    "/list",
    response_model=PaginatedResponse[RoleModel],
    dependencies=[Depends(RequirePermission(Permissions.ROLE_READ))],
)
async def get_role_list_by_filter(
    data: FilterRoleRequest,
    uow=Depends(get_uow),
) -> PaginatedResponse[RoleModel]:
    usecase = GetRoleListByFilterUseCase(uow)

    res = await usecase.execute(RoleApiMapper.to_get_list_role_dto(data))

    return RoleApiMapper.from_get_list_role_dto(res)
