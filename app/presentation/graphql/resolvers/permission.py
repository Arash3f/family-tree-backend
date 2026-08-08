from strawberry.types import Info

from app.application.use_cases.permission.get_permission_list_by_filter_use_case import (
    GetPermissionListByFilterUseCase,
)
from app.infrastructure.utils.constants.permissions import Permissions
from app.presentation.graphql.auth import require_permission
from app.presentation.graphql.types.common import (
    pagination_dict,
    permission_sort_field,
    to_sort_order,
)
from app.presentation.graphql.types.permission import (
    PermissionListInput,
    PermissionPage,
    permission_from_mapping,
)
from app.presentation.rest.schemas.dto.common import (
    PaginationRequestParams,
    SortRequestParams,
)
from app.presentation.rest.schemas.dto.permission_schema import (
    FilterPermissionRequest,
    PermissionFilterRequestData,
)
from app.presentation.rest.schemas.mappers.permission_mappers import PermissionApiMapper


def _permission_list_request(
    data: PermissionListInput | None,
) -> FilterPermissionRequest:
    payload = data or PermissionListInput()
    filters = None
    if payload.filters is not None:
        f = payload.filters
        filters = PermissionFilterRequestData(id=f.id, name=f.name)
    return FilterPermissionRequest(
        pagination=PaginationRequestParams(**pagination_dict(payload.pagination)),
        filters=filters,
        sort=SortRequestParams(
            sort_order=to_sort_order(payload.sort_order),
            sort_by=permission_sort_field(payload.sort_by),
        ),
    )


async def resolve_permissions(
    info: Info, data: PermissionListInput | None = None
) -> PermissionPage:
    await require_permission(info, Permissions.PERMISSION_READ)
    usecase = GetPermissionListByFilterUseCase(info.context.uow)
    res = await usecase.execute(
        PermissionApiMapper.to_get_list_permission_dto(_permission_list_request(data))
    )
    mapped = PermissionApiMapper.from_get_list_permission_dto(res)
    return PermissionPage(
        items=[permission_from_mapping(item.model_dump()) for item in mapped.items],
        total=mapped.total,
        page=mapped.page,
        page_size=mapped.page_size,
    )
