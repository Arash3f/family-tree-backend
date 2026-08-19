from uuid import UUID

from app.application.dto.ticket.ticket_add_message_dto import TicketAddMessageDTO
from app.application.dto.ticket.ticket_create_dto import TicketCreateDTO
from app.application.dto.ticket.ticket_get_dto import TicketGetDTO
from app.application.dto.ticket.ticket_list_dto import TicketListDTO
from app.application.dto.ticket.ticket_response_dto import (
    TicketDetailResponseDTO,
    TicketMessageResponseDTO,
    TicketSummaryResponseDTO,
)
from app.application.dto.ticket.ticket_update_status_dto import TicketUpdateStatusDTO
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.ticket_filter_dto import FilterTicketQuery
from app.presentation.rest.schemas.dto.common import PaginatedResponse
from app.presentation.rest.schemas.dto.ticket_schema import (
    FilterTicketRequest,
    TicketCreateRequest,
    TicketCreateResponse,
    TicketDetailModel,
    TicketGetResponse,
    TicketMessageCreateRequest,
    TicketMessageCreateResponse,
    TicketMessageModel,
    TicketSummaryModel,
    TicketUpdateStatusRequest,
    TicketUpdateStatusResponse,
)


class TicketApiMapper:
    @staticmethod
    def to_create_ticket_dto(
        request: TicketCreateRequest, created_by_user_id: UUID
    ) -> TicketCreateDTO:
        return TicketCreateDTO(
            title=request.title,
            body=request.body,
            category=request.category,
            family_tree_id=request.family_tree_id,
            created_by_user_id=created_by_user_id,
        )

    @staticmethod
    def from_create_ticket_dto(
        response: TicketDetailResponseDTO,
    ) -> TicketCreateResponse:
        return TicketCreateResponse.model_validate(response.model_dump())

    @staticmethod
    def to_get_ticket_dto(
        ticket_id: UUID, current_user_id: UUID, can_manage: bool
    ) -> TicketGetDTO:
        return TicketGetDTO(
            ticket_id=ticket_id,
            current_user_id=current_user_id,
            can_manage=can_manage,
        )

    @staticmethod
    def from_get_ticket_dto(response: TicketDetailResponseDTO) -> TicketGetResponse:
        return TicketGetResponse.model_validate(response.model_dump())

    @staticmethod
    def to_list_ticket_dto(
        request: FilterTicketRequest, current_user_id: UUID, can_manage: bool
    ) -> TicketListDTO:
        query = FilterTicketQuery.model_validate(request.model_dump())
        return TicketListDTO(
            query=query,
            current_user_id=current_user_id,
            can_manage=can_manage,
        )

    @staticmethod
    def from_list_ticket_dto(
        response: PaginatedResult[TicketSummaryResponseDTO],
    ) -> PaginatedResponse[TicketSummaryModel]:
        items = [
            TicketSummaryModel.model_validate(item.model_dump())
            for item in response.items
        ]
        return PaginatedResponse[TicketSummaryModel](
            page=response.page,
            page_size=response.page_size,
            total=response.total,
            items=items,
        )

    @staticmethod
    def to_add_message_dto(
        ticket_id: UUID,
        request: TicketMessageCreateRequest,
        author_user_id: UUID,
        can_manage: bool,
    ) -> TicketAddMessageDTO:
        return TicketAddMessageDTO(
            ticket_id=ticket_id,
            author_user_id=author_user_id,
            body=request.body,
            can_manage=can_manage,
        )

    @staticmethod
    def from_add_message_dto(
        response: TicketMessageResponseDTO,
    ) -> TicketMessageCreateResponse:
        return TicketMessageCreateResponse.model_validate(response.model_dump())

    @staticmethod
    def to_update_status_dto(
        ticket_id: UUID,
        request: TicketUpdateStatusRequest,
        current_user_id: UUID,
        can_manage: bool,
    ) -> TicketUpdateStatusDTO:
        return TicketUpdateStatusDTO(
            ticket_id=ticket_id,
            status=request.status,
            current_user_id=current_user_id,
            can_manage=can_manage,
        )

    @staticmethod
    def from_update_status_dto(
        response: TicketSummaryResponseDTO,
    ) -> TicketUpdateStatusResponse:
        return TicketUpdateStatusResponse.model_validate(response.model_dump())

    @staticmethod
    def from_detail(response: TicketDetailResponseDTO) -> TicketDetailModel:
        return TicketDetailModel.model_validate(response.model_dump())

    @staticmethod
    def from_message(response: TicketMessageResponseDTO) -> TicketMessageModel:
        return TicketMessageModel.model_validate(response.model_dump())
