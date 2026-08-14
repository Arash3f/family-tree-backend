from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from app.application.dto.ticket.ticket_add_message_dto import TicketAddMessageDTO
from app.application.dto.ticket.ticket_create_dto import TicketCreateDTO
from app.application.dto.ticket.ticket_get_dto import TicketGetDTO
from app.application.dto.ticket.ticket_list_dto import TicketListDTO
from app.application.dto.ticket.ticket_update_status_dto import TicketUpdateStatusDTO
from app.application.use_cases.ticket.add_ticket_message_use_case import (
    AddTicketMessageUseCase,
)
from app.application.use_cases.ticket.create_ticket_use_case import CreateTicketUseCase
from app.application.use_cases.ticket.get_ticket_list_by_filter_use_case import (
    GetTicketListByFilterUseCase,
)
from app.application.use_cases.ticket.get_ticket_use_case import GetTicketUseCase
from app.application.use_cases.ticket.update_ticket_status_use_case import (
    UpdateTicketStatusUseCase,
)
from app.domain.entities.ticket import Ticket
from app.domain.entities.ticket_message import TicketMessage
from app.domain.exceptions.ticket_exceptions import (
    TicketAccessDeniedException,
    TicketClosedException,
)
from app.domain.shared.dto.pagination_dto import PaginatedResult, PaginationParams
from app.domain.shared.dto.sorter_dto import SortOrderField, SortParams
from app.domain.shared.dto.ticket_filter_dto import (
    FilterTicketQuery,
    TicketFilterDTO,
    TicketSortField,
)
from app.domain.shared.enums.ticket_category import TicketCategory
from app.domain.shared.enums.ticket_status import TicketStatus


@pytest.mark.asyncio
async def test_create_ticket(mock_uow):
    user_id = UUID(int=10)
    ticket_id = UUID(int=20)
    message_id = UUID(int=30)
    now = datetime.now(timezone.utc)

    created_ticket = Ticket(
        id=ticket_id,
        title="Help",
        status=TicketStatus.OPEN,
        category=TicketCategory.GENERAL,
        created_by_user_id=user_id,
        created_at=now,
        updated_at=now,
    )
    created_message = TicketMessage(
        id=message_id,
        ticket_id=ticket_id,
        author_user_id=user_id,
        body="I need help",
        created_at=now,
        updated_at=now,
    )

    mock_uow.tickets.create = AsyncMock(return_value=created_ticket)
    mock_uow.ticket_messages.create = AsyncMock(return_value=created_message)
    mock_uow.users.ids_having_permission = AsyncMock(return_value=set())

    dto = TicketCreateDTO(
        title="Help",
        body="I need help",
        category=TicketCategory.GENERAL,
        created_by_user_id=user_id,
    )
    result = await CreateTicketUseCase(mock_uow).execute(dto)

    assert result.id == ticket_id
    assert result.title == "Help"
    assert result.status == TicketStatus.OPEN
    assert result.category == TicketCategory.GENERAL
    assert len(result.messages) == 1
    assert result.messages[0].body == "I need help"
    assert result.created_by_can_manage is False
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_ticket_owner_ok(mock_uow):
    user_id = UUID(int=10)
    ticket_id = UUID(int=20)
    ticket = Ticket(
        id=ticket_id,
        title="Help",
        status=TicketStatus.OPEN,
        category=TicketCategory.ACCOUNT,
        created_by_user_id=user_id,
    )
    mock_uow.tickets.get_or_raise = AsyncMock(return_value=ticket)
    mock_uow.ticket_messages.get_by_ticket_id = AsyncMock(return_value=[])
    mock_uow.users.ids_having_permission = AsyncMock(return_value=set())

    result = await GetTicketUseCase(mock_uow).execute(
        TicketGetDTO(ticket_id=ticket_id, current_user_id=user_id, can_manage=False)
    )

    assert result.id == ticket_id
    assert result.created_by_can_manage is False


@pytest.mark.asyncio
async def test_get_ticket_access_denied(mock_uow):
    owner_id = UUID(int=10)
    other_id = UUID(int=11)
    ticket_id = UUID(int=20)
    ticket = Ticket(
        id=ticket_id,
        title="Help",
        status=TicketStatus.OPEN,
        category=TicketCategory.GENERAL,
        created_by_user_id=owner_id,
    )
    mock_uow.tickets.get_or_raise = AsyncMock(return_value=ticket)

    with pytest.raises(TicketAccessDeniedException):
        await GetTicketUseCase(mock_uow).execute(
            TicketGetDTO(
                ticket_id=ticket_id, current_user_id=other_id, can_manage=False
            )
        )


@pytest.mark.asyncio
async def test_list_tickets_scopes_to_owner(mock_uow):
    user_id = UUID(int=10)
    ticket = Ticket(
        id=UUID(int=20),
        title="Mine",
        status=TicketStatus.OPEN,
        category=TicketCategory.TECHNICAL,
        created_by_user_id=user_id,
    )
    mock_uow.tickets.get_list_by_filter = AsyncMock(
        return_value=PaginatedResult(items=[ticket], total=1, page=1, page_size=30)
    )
    mock_uow.users.ids_having_permission = AsyncMock(return_value=set())

    query = FilterTicketQuery(
        pagination=PaginationParams(page=1, page_size=30, offset=0),
        filters=TicketFilterDTO(),
        sort=SortParams(
            sort_order=SortOrderField.DESC, sort_by=TicketSortField.CREATED_AT
        ),
    )
    result = await GetTicketListByFilterUseCase(mock_uow).execute(
        TicketListDTO(query=query, current_user_id=user_id, can_manage=False)
    )

    assert result.total == 1
    assert result.items[0].created_by_can_manage is False
    called_query = mock_uow.tickets.get_list_by_filter.await_args.kwargs["query"]
    assert called_query.filters.created_by_user_id == user_id


@pytest.mark.asyncio
async def test_add_consecutive_messages_from_same_author(mock_uow):
    user_id = UUID(int=10)
    ticket_id = UUID(int=20)
    now = datetime.now(timezone.utc)
    ticket = Ticket(
        id=ticket_id,
        title="Help",
        status=TicketStatus.OPEN,
        category=TicketCategory.GENERAL,
        created_by_user_id=user_id,
    )
    first = TicketMessage(
        id=UUID(int=31),
        ticket_id=ticket_id,
        author_user_id=user_id,
        body="First follow-up",
        created_at=now,
        updated_at=now,
    )
    second = TicketMessage(
        id=UUID(int=32),
        ticket_id=ticket_id,
        author_user_id=user_id,
        body="Second follow-up",
        created_at=now,
        updated_at=now,
    )
    mock_uow.tickets.get_or_raise = AsyncMock(return_value=ticket)
    mock_uow.ticket_messages.create = AsyncMock(side_effect=[first, second])

    usecase = AddTicketMessageUseCase(mock_uow)
    result_one = await usecase.execute(
        TicketAddMessageDTO(
            ticket_id=ticket_id,
            author_user_id=user_id,
            body="First follow-up",
            can_manage=False,
        )
    )
    result_two = await usecase.execute(
        TicketAddMessageDTO(
            ticket_id=ticket_id,
            author_user_id=user_id,
            body="Second follow-up",
            can_manage=False,
        )
    )

    assert result_one.body == "First follow-up"
    assert result_two.body == "Second follow-up"
    assert mock_uow.ticket_messages.create.await_count == 2
    assert mock_uow.commit.await_count == 2


@pytest.mark.asyncio
async def test_add_message_on_closed_ticket(mock_uow):
    user_id = UUID(int=10)
    ticket_id = UUID(int=20)
    ticket = Ticket(
        id=ticket_id,
        title="Help",
        status=TicketStatus.CLOSED,
        category=TicketCategory.BUG,
        created_by_user_id=user_id,
    )
    mock_uow.tickets.get_or_raise = AsyncMock(return_value=ticket)

    with pytest.raises(TicketClosedException):
        await AddTicketMessageUseCase(mock_uow).execute(
            TicketAddMessageDTO(
                ticket_id=ticket_id,
                author_user_id=user_id,
                body="more",
                can_manage=False,
            )
        )


@pytest.mark.asyncio
async def test_update_ticket_status(mock_uow):
    ticket_id = UUID(int=20)
    user_id = UUID(int=10)
    ticket = Ticket(
        id=ticket_id,
        title="Help",
        status=TicketStatus.OPEN,
        category=TicketCategory.OTHER,
        created_by_user_id=user_id,
    )
    updated = Ticket(
        id=ticket_id,
        title="Help",
        status=TicketStatus.IN_PROGRESS,
        category=TicketCategory.OTHER,
        created_by_user_id=user_id,
    )
    mock_uow.tickets.get_or_raise = AsyncMock(return_value=ticket)
    mock_uow.tickets.update = AsyncMock(return_value=updated)
    mock_uow.users.ids_having_permission = AsyncMock(return_value=set())

    result = await UpdateTicketStatusUseCase(mock_uow).execute(
        TicketUpdateStatusDTO(ticket_id=ticket_id, status=TicketStatus.IN_PROGRESS)
    )
    assert result.status == TicketStatus.IN_PROGRESS
    assert result.created_by_can_manage is False
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_marks_staff_created_tickets(mock_uow):
    staff_id = UUID(int=10)
    ticket = Ticket(
        id=UUID(int=20),
        title="Internal",
        status=TicketStatus.OPEN,
        category=TicketCategory.TECHNICAL,
        created_by_user_id=staff_id,
    )
    mock_uow.tickets.get_list_by_filter = AsyncMock(
        return_value=PaginatedResult(items=[ticket], total=1, page=1, page_size=30)
    )
    mock_uow.users.ids_having_permission = AsyncMock(return_value={staff_id})

    query = FilterTicketQuery(
        pagination=PaginationParams(page=1, page_size=30, offset=0),
        filters=TicketFilterDTO(),
        sort=SortParams(
            sort_order=SortOrderField.DESC, sort_by=TicketSortField.CREATED_AT
        ),
    )
    result = await GetTicketListByFilterUseCase(mock_uow).execute(
        TicketListDTO(query=query, current_user_id=staff_id, can_manage=True)
    )

    assert result.items[0].created_by_can_manage is True
