import pytest

from app.domain.entities.user import User
from app.infrastructure.database.models import TicketMessageModel, TicketModel
from app.infrastructure.services.security.password_hasher_impl import (
    Argon2PasswordHasher,
)


@pytest.mark.asyncio
async def test_ticket_and_message_persist(uow):
    hasher = Argon2PasswordHasher()
    user = await uow.users.create(
        User(username="ticket_owner", password_hash=hasher.hash("pass"))
    )
    await uow.commit()

    ticket = TicketModel(
        title="Need help",
        status="open",
        category="general",
        created_by_user_id=user.safe_id,
    )
    uow.session.add(ticket)
    await uow.session.flush()

    message = TicketMessageModel(
        ticket_id=ticket.id,
        author_user_id=user.safe_id,
        body="First message",
    )
    uow.session.add(message)
    await uow.session.flush()

    assert ticket.id is not None
    assert message.ticket_id == ticket.id
    assert message.body == "First message"
