from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.ticket_message import TicketMessage
from app.domain.repositories.ticket_message_repository import TicketMessageRepository
from app.infrastructure.database.models.ticket_message_model import TicketMessageModel


class SQLTicketMessageRepository(TicketMessageRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, message: TicketMessage) -> TicketMessage:
        model = TicketMessageModel(
            ticket_id=message.ticket_id,
            author_user_id=message.author_user_id,
            body=message.body,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_by_ticket_id(self, ticket_id: UUID) -> list[TicketMessage]:
        stmt = (
            select(TicketMessageModel)
            .where(TicketMessageModel.ticket_id == ticket_id)
            .order_by(TicketMessageModel.created_at.asc())
        )
        result = await self.session.execute(stmt)
        models = list(result.scalars().all())
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: TicketMessageModel) -> TicketMessage:
        return TicketMessage(
            id=model.id,
            ticket_id=model.ticket_id,
            author_user_id=model.author_user_id,
            body=model.body,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
