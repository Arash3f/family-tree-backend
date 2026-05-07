from app.application.dto.role.role_create_dto import (
    RoleCreateDTO,
    RoleCreateResponseDTO,
)
from app.application.dto.role.role_get_dto import RoleGetResponseDTO
from app.application.dto.role.role_update_dto import (
    RoleUpdateDTO,
    RoleUpdateResponseDTO,
)
from app.domain.entities.role import Role
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.role_filter_dto import FilterRoleQuery
from app.presentation.rest.schemas.dto.common import PaginatedResponse
from app.presentation.rest.schemas.dto.role_schema import (
    FilterRoleRequest,
    RoleCreateRequest,
    RoleCreateResponse,
    RoleGetResponse,
    RoleModel,
    RoleUpdateRequest,
    RoleUpdateResponse,
)


class RoleApiMapper:
    @staticmethod
    def to_create_role_dto(request: RoleCreateRequest) -> RoleCreateDTO:
        request_data = request.model_dump()
        return RoleCreateDTO.model_validate(request_data)

    @staticmethod
    def from_create_role_dto(
        response: RoleCreateResponseDTO,
    ) -> RoleCreateResponse:
        response_data = response.model_dump()
        return RoleCreateResponse.model_validate(response_data)

    @staticmethod
    def to_update_role_dto(request: RoleUpdateRequest) -> RoleUpdateDTO:
        request_data = request.model_dump()
        return RoleUpdateDTO.model_validate(request_data)

    @staticmethod
    def from_update_role_dto(
        response: RoleUpdateResponseDTO,
    ) -> RoleUpdateResponse:
        response_data = response.model_dump()
        return RoleUpdateResponse.model_validate(response_data)

    @staticmethod
    def from_get_role_dto(response: RoleGetResponseDTO) -> RoleGetResponse:
        response_data = response.model_dump()
        return RoleGetResponse.model_validate(response_data)

    @staticmethod
    def to_get_list_role_dto(request: FilterRoleRequest) -> FilterRoleQuery:
        data = request.model_dump()

        return FilterRoleQuery.model_validate(data)

    @staticmethod
    def from_get_list_role_dto(
        response: PaginatedResult[Role],
    ) -> PaginatedResponse[RoleModel]:
        items = [
            RoleModel.model_validate(item, from_attributes=True)
            for item in response.items
        ]

        return PaginatedResponse[RoleModel](
            page=response.page,
            page_size=response.page_size,
            total=response.total,
            items=items,
        )
