from app.application.dto.user.user_create_dto import (
    UserCreateDTO,
    UserCreateResponseDTO,
)
from app.application.dto.user.user_get_dto import UserGetResponseDTO
from app.application.dto.user.user_update_dto import (
    UserUpdateDTO,
    UserUpdateResponseDTO,
)
from app.domain.entities.user import User
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.user_filter_dto import FilterUserQuery
from app.presentation.rest.schemas.dto.common import PaginatedResponse
from app.presentation.rest.schemas.dto.user_schema import (
    FilterUserRequest,
    UserCreateRequest,
    UserCreateResponse,
    UserGetResponse,
    UserModel,
    UserUpdateRequest,
    UserUpdateResponse,
)


class UserApiMapper:
    @staticmethod
    def to_create_user_dto(request: UserCreateRequest) -> UserCreateDTO:
        request_data = request.model_dump()
        return UserCreateDTO.model_validate(request_data)

    @staticmethod
    def from_create_user_dto(
        response: UserCreateResponseDTO,
    ) -> UserCreateResponse:
        response_data = response.model_dump()
        return UserCreateResponse.model_validate(response_data)

    @staticmethod
    def to_update_user_dto(request: UserUpdateRequest) -> UserUpdateDTO:
        request_data = request.model_dump()
        return UserUpdateDTO.model_validate(request_data)

    @staticmethod
    def from_update_user_dto(
        response: UserUpdateResponseDTO,
    ) -> UserUpdateResponse:
        response_data = response.model_dump()
        return UserUpdateResponse.model_validate(response_data)

    @staticmethod
    def from_get_user_dto(response: UserGetResponseDTO) -> UserGetResponse:
        response_data = response.model_dump()
        return UserGetResponse.model_validate(response_data)

    @staticmethod
    def to_get_list_user_dto(request: FilterUserRequest) -> FilterUserQuery:
        data = request.model_dump()

        return FilterUserQuery.model_validate(data)

    @staticmethod
    def from_get_list_user_dto(
        response: PaginatedResult[User],
    ) -> PaginatedResponse[UserModel]:
        items = [
            UserModel.model_validate(item, from_attributes=True)
            for item in response.items
        ]

        return PaginatedResponse[UserModel](
            page=response.page,
            page_size=response.page_size,
            total=response.total,
            items=items,
        )
