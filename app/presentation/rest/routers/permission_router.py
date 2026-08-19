from fastapi import APIRouter, Depends

from app.application.use_cases.permission import get_permission_list_by_filter_use_case
from app.domain.shared.permissions import Permissions
from app.presentation.dependencies import get_request_uow
from app.presentation.rest.dependencies.permission_guard import RequirePermission
from app.presentation.rest.schemas.dto.common import PaginatedResponse
from app.presentation.rest.schemas.dto.permission_schema import (
    FilterPermissionRequest,
    PermissionModel,
)
from app.presentation.rest.schemas.mappers.permission_mappers import PermissionApiMapper

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.post(
    "/list",
    response_model=PaginatedResponse[PermissionModel],
    dependencies=[Depends(RequirePermission(Permissions.PERMISSION_READ))],
)
async def get_permission_list_by_filter(
    data: FilterPermissionRequest,
    uow=Depends(get_request_uow),
) -> PaginatedResponse[PermissionModel]:
    usecase = get_permission_list_by_filter_use_case.GetPermissionListByFilterUseCase(
        uow
    )

    res = await usecase.execute(PermissionApiMapper.to_get_list_permission_dto(data))

    return PermissionApiMapper.from_get_list_permission_dto(res)
