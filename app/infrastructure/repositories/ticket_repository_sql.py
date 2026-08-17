from collections.abc import Mapping
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.ticket import Ticket
from app.domain.repositories.ticket_repository import TicketRepository
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.ticket_filter_dto import FilterTicketQuery, TicketSortField
from app.domain.shared.enums.ticket_category import TicketCategory
from app.domain.shared.enums.ticket_status import TicketStatus
from app.infrastructure.database.models.ticket_model import TicketModel
from app.infrastructure.database.utils.pagination_and_sort import paginate_and_sort


class SQLTicketRepository(TicketRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, ticket: Ticket) -> Ticket:
        model = TicketModel(
            title=ticket.title,
            status=ticket.status.value,
            category=ticket.category.value,
            created_by_user_id=ticket.created_by_user_id,
            family_tree_id=ticket.family_tree_id,
        )
        self.session.add(model)
        await self.session.flush()
        created = await self.get(model.id)
        if created is None:
            raise RuntimeError("ticket missing after create")
        return created

    async def get(self, ticket_id: UUID) -> Ticket | None:
        stmt = (
            select(TicketModel)
            .options(selectinload(TicketModel.family_tree))
            .where(TicketModel.id == ticket_id)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def get_list_by_filter(
        self, query: FilterTicketQuery
    ) -> PaginatedResult[Ticket]:
        stmt = select(TicketModel).options(selectinload(TicketModel.family_tree))
        filters = query.filters

        if filters:
            if filters.id:
                stmt = stmt.where(TicketModel.id == filters.id)
            if filters.title:
                stmt = stmt.where(TicketModel.title.contains(filters.title, autoescape=True))
            if filters.status is not None:
                stmt = stmt.where(TicketModel.status == filters.status.value)
            if filters.category is not None:
                stmt = stmt.where(TicketModel.category == filters.category.value)
            if filters.family_tree_id is not None:
                stmt = stmt.where(TicketModel.family_tree_id == filters.family_tree_id)
            if filters.created_by_user_id is not None:
                stmt = stmt.where(
                    TicketModel.created_by_user_id == filters.created_by_user_id
                )

        SORTABLE_COLUMNS: Mapping[Enum, Any] = {
            TicketSortField.ID: TicketModel.id,
            TicketSortField.TITLE: TicketModel.title,
            TicketSortField.STATUS: TicketModel.status,
            TicketSortField.CATEGORY: TicketModel.category,
            TicketSortField.CREATED_AT: TicketModel.created_at,
            TicketSortField.UPDATED_AT: TicketModel.updated_at,
        }

        result = await paginate_and_sort(
            model=TicketModel,
            stmt=stmt,
            session=self.session,
            page=query.pagination.page,
            page_size=query.pagination.page_size,
            sort_by=query.sort.sort_by,
            offset=query.pagination.offset,
            sort_order=query.sort.sort_order,
            sortable_columns=SORTABLE_COLUMNS,
        )

        tickets = [self._to_entity(m) for m in result.items]
        return PaginatedResult[Ticket](
            items=tickets,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )

    async def update(self, ticket: Ticket) -> Ticket:
        stmt = (
            select(TicketModel)
            .options(selectinload(TicketModel.family_tree))
            .where(TicketModel.id == ticket.id)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one()

        model.title = ticket.title
        model.status = ticket.status.value
        model.category = ticket.category.value
        model.created_by_user_id = ticket.created_by_user_id
        model.family_tree_id = ticket.family_tree_id

        await self.session.flush()
        await self.session.refresh(model, attribute_names=["family_tree"])
        return self._to_entity(model)

    def _to_entity(self, model: TicketModel) -> Ticket:
        tree_name = None
        if model.family_tree is not None:
            tree_name = model.family_tree.name
        return Ticket(
            id=model.id,
            title=model.title,
            status=TicketStatus(model.status),
            category=TicketCategory(model.category),
            created_by_user_id=model.created_by_user_id,
            family_tree_id=model.family_tree_id,
            family_tree_name=tree_name,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
