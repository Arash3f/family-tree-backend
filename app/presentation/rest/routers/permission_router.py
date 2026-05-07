from fastapi import APIRouter, Depends

from app.application.use_cases.permission.get_permission_list_by_filter_use_case import (
    GetPermissionListByFilterUseCase,
)
from app.domain.constants.permissions import Permissions
from app.presentation.rest.utils.dependencies import get_uow
from app.presentation.rest.schemas.dto.common import PaginatedResponse
from app.presentation.rest.schemas.dto.permission_schema import (
    FilterPermissionRequest,
    PermissionModel,
)
from app.presentation.rest.schemas.mappers.permission_mappers import PermissionApiMapper
from app.presentation.rest.dependencies.permission_guard import RequirePermission


router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.post(
    "/list",
    response_model=PaginatedResponse[PermissionModel],
    dependencies=[Depends(RequirePermission(Permissions.PERMISSION_READ))],
)
async def get_permission_list_by_filter(
    data: FilterPermissionRequest,
    uow=Depends(get_uow),
) -> PaginatedResponse[PermissionModel]:
    usecase = GetPermissionListByFilterUseCase(uow)

    res = await usecase.execute(PermissionApiMapper.to_get_list_permission_dto(data))

    return PermissionApiMapper.from_get_list_permission_dto(res)
