from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.domain.shared.dto.pagination_dto import PaginationParams
from app.domain.shared.dto.sorter_dto import SortParams
from app.domain.shared.enums.ticket_category import TicketCategory
from app.domain.shared.enums.ticket_status import TicketStatus


class TicketSortField(StrEnum):
    ID = "id"
    TITLE = "title"
    STATUS = "status"
    CATEGORY = "category"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class TicketFilterDTO(BaseModel):
    id: UUID | None = None
    title: str | None = None
    status: TicketStatus | None = None
    category: TicketCategory | None = None
    family_tree_id: UUID | None = None
    created_by_user_id: UUID | None = None


class TicketAccessScopeDTO(BaseModel):
    """Restricts results to tickets the user may see.

    Applied as:
      (created_by_user_id == owner_user_id)
      OR (family_tree_id IN manageable_tree_ids)
      OR (include_unlinked AND family_tree_id IS NULL)

    ``include_unlinked`` is for system ``ticket_reply`` (global support queue).
    Tree-linked tickets are never opened by that flag alone.
    """

    owner_user_id: UUID
    manageable_tree_ids: list[UUID] = []
    include_unlinked: bool = False


class FilterTicketQuery(BaseModel):
    pagination: PaginationParams
    filters: TicketFilterDTO | None = None
    access_scope: TicketAccessScopeDTO | None = None
    sort: SortParams[TicketSortField]
