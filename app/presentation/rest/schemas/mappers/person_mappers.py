from app.application.dto.person.person_create_dto import (
    PersonCreateDTO,
    PersonCreateResponseDTO,
)
from app.application.dto.person.person_get_dto import PersonGetResponseDTO
from app.application.dto.person.person_update_dto import (
    PersonUpdateDTO,
    PersonUpdateResponseDTO,
)
from app.domain.entities.person import Person
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.person_filter_dto import FilterPersonQuery
from app.presentation.rest.schemas.dto.common import PaginatedResponse
from app.presentation.rest.schemas.dto.person_schema import (
    FilterPersonRequest,
    PersonCreateRequest,
    PersonCreateResponse,
    PersonGetResponse,
    PersonModel,
    PersonUpdateRequest,
    PersonUpdateResponse,
)


class PersonApiMapper:
    @staticmethod
    def to_create_person_dto(request: PersonCreateRequest) -> PersonCreateDTO:
        request_data = request.model_dump()
        return PersonCreateDTO.model_validate(request_data)

    @staticmethod
    def from_create_person_dto(
        response: PersonCreateResponseDTO,
    ) -> PersonCreateResponse:
        response_data = response.model_dump()
        return PersonCreateResponse.model_validate(response_data)

    @staticmethod
    def to_update_person_dto(request: PersonUpdateRequest) -> PersonUpdateDTO:
        request_data = request.model_dump()
        return PersonUpdateDTO.model_validate(request_data)

    @staticmethod
    def from_update_person_dto(
        response: PersonUpdateResponseDTO,
    ) -> PersonUpdateResponse:
        response_data = response.model_dump()
        return PersonUpdateResponse.model_validate(response_data)

    @staticmethod
    def from_get_person_dto(response: PersonGetResponseDTO) -> PersonGetResponse:
        response_data = response.model_dump()
        return PersonGetResponse.model_validate(response_data)

    @staticmethod
    def to_get_list_person_dto(request: FilterPersonRequest) -> FilterPersonQuery:
        data = request.model_dump()

        if request.filters.birth_date is not None:
            data["filters"]["birth_date"] = {
                "min": request.filters.birth_date.min,
                "max": request.filters.birth_date.max,
            }

        return FilterPersonQuery.model_validate(data)

    @staticmethod
    def from_get_list_person_dto(
        response: PaginatedResult[Person],
    ) -> PaginatedResponse[PersonModel]:
        items = [
            PersonModel.model_validate(item, from_attributes=True)
            for item in response.items
        ]

        return PaginatedResponse[PersonModel](
            page=response.page,
            page_size=response.page_size,
            total=response.total,
            items=items,
        )
