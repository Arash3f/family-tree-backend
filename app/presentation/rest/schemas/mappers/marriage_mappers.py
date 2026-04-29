from app.application.dto.marriage.divorce_dto import DivorceDTO
from app.application.dto.marriage.marriage_create_dto import (
    MarriageCreateDTO,
    MarriageCreateResponseDTO,
)
from app.application.dto.marriage.marriage_get_dto import MarriageGetResponseDTO
from app.application.dto.marriage.marriage_update_dto import (
    MarriageUpdateDTO,
    MarriageUpdateResponseDTO,
)
from app.domain.entities.marriage import Marriage
from app.domain.shared.dto.marriage_filter_dto import FilterMarriageDTO
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.presentation.rest.schemas.dto.common import PaginatedResponse
from app.presentation.rest.schemas.dto.marriage_schema import (
    DivorceRequest,
    FilterMarriageRequest,
    MarriageCreateRequest,
    MarriageCreateResponse,
    MarriageGetResponse,
    MarriageModel,
    MarriageUpdateRequest,
    MarriageUpdateResponse,
)


class MarriageApiMapper:
    @staticmethod
    def to_create_marriage_dto(request: MarriageCreateRequest) -> MarriageCreateDTO:
        request_data = request.model_dump()
        return MarriageCreateDTO.model_validate(request_data)

    @staticmethod
    def from_create_marriage_dto(
        response: MarriageCreateResponseDTO,
    ) -> MarriageCreateResponse:
        response_data = response.model_dump()
        return MarriageCreateResponse.model_validate(response_data)

    @staticmethod
    def to_update_marriage_dto(request: MarriageUpdateRequest) -> MarriageUpdateDTO:
        request_data = request.model_dump()
        return MarriageUpdateDTO.model_validate(request_data)

    @staticmethod
    def from_update_marriage_dto(
        response: MarriageUpdateResponseDTO,
    ) -> MarriageUpdateResponse:
        response_data = response.model_dump()
        return MarriageUpdateResponse.model_validate(response_data)

    @staticmethod
    def from_get_marriage_dto(response: MarriageGetResponseDTO) -> MarriageGetResponse:
        response_data = response.model_dump()
        return MarriageGetResponse.model_validate(response_data)

    @staticmethod
    def to_get_list_marriage_dto(request: FilterMarriageRequest) -> FilterMarriageDTO:
        data = request.model_dump()

        if request.filters.married_at is not None:
            data["filters"]["married_at"] = {
                "min": request.filters.married_at.min,
                "max": request.filters.married_at.max,
            }
        if request.filters.divorced_at is not None:
            data["filters"]["divorced_at"] = {
                "min": request.filters.divorced_at.min,
                "max": request.filters.divorced_at.max,
            }

        return FilterMarriageDTO.model_validate(data)

    @staticmethod
    def from_get_list_marriage_dto(
        response: PaginatedResult[Marriage],
    ) -> PaginatedResponse[MarriageModel]:
        items = [
            MarriageModel.model_validate(item, from_attributes=True)
            for item in response.items
        ]

        return PaginatedResponse[MarriageModel](
            page=response.page,
            page_size=response.page_size,
            total=response.total,
            items=items,
        )

    @staticmethod
    def to_add_divorce_dto(request: DivorceRequest) -> DivorceDTO:
        return DivorceDTO(
            marriage_id=request.marriage_id, divorced_at=request.divorced_at
        )
