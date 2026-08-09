from uuid import UUID

from pydantic import BaseModel

from app.domain.shared.dto.ticket_filter_dto import FilterTicketQuery


class TicketListDTO(BaseModel):
    query: FilterTicketQuery
    current_user_id: UUID
    can_manage: bool = False
