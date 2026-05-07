from app.domain.entities.permission import Permission
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.permission_filter_dto import FilterPermissionQuery
from app.presentation.rest.schemas.dto.common import PaginatedResponse
from app.presentation.rest.schemas.dto.permission_schema import (
    FilterPermissionRequest,
    PermissionModel,
)


class PermissionApiMapper:
    @staticmethod
    def to_get_list_permission_dto(
        request: FilterPermissionRequest,
    ) -> FilterPermissionQuery:
        data = request.model_dump()
        return FilterPermissionQuery.model_validate(data)

    @staticmethod
    def from_get_list_permission_dto(
        response: PaginatedResult[Permission],
    ) -> PaginatedResponse[PermissionModel]:
        items = [
            PermissionModel.model_validate(item, from_attributes=True)
            for item in response.items
        ]

        return PaginatedResponse[PermissionModel](
            page=response.page,
            page_size=response.page_size,
            total=response.total,
            items=items,
        )
