from uuid import UUID

from strawberry.types import Info

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
from app.domain.shared.permissions import Permissions
from app.presentation.graphql.auth import require_permission
from app.presentation.graphql.types.common import pagination_dict, to_sort_order
from app.presentation.graphql.types.ticket import (
    TicketCreateInput,
    TicketListInput,
    TicketMessageCreateInput,
    TicketMessageType,
    TicketPage,
    TicketSummaryType,
    TicketType,
    TicketUpdateStatusInput,
    ticket_from_mapping,
    ticket_message_from_mapping,
    ticket_sort_field,
    ticket_summary_from_mapping,
    to_domain_ticket_status,
)
from app.presentation.rest.schemas.dto.common import (
    PaginationRequestParams,
    SortRequestParams,
)
from app.presentation.rest.schemas.dto.ticket_schema import (
    FilterTicketRequest,
    TicketCreateRequest,
    TicketFilterRequestData,
    TicketMessageCreateRequest,
    TicketUpdateStatusRequest,
)
from app.presentation.rest.schemas.mappers.ticket_mappers import TicketApiMapper


async def _can_manage(info: Info, user_id: UUID) -> bool:
    return await info.context.authorization_service.user_has_permission(
        user_id, Permissions.TICKET_MANAGE
    )


def _ticket_list_request(data: TicketListInput | None) -> FilterTicketRequest:
    payload = data or TicketListInput()
    filters = None
    if payload.filters is not None:
        f = payload.filters
        filters = TicketFilterRequestData(
            id=f.id,
            title=f.title,
            status=to_domain_ticket_status(f.status) if f.status else None,
            created_by_user_id=f.created_by_user_id,
        )
    return FilterTicketRequest(
        pagination=PaginationRequestParams(**pagination_dict(payload.pagination)),
        filters=filters,
        sort=SortRequestParams(
            sort_order=to_sort_order(payload.sort_order),
            sort_by=ticket_sort_field(payload.sort_by),
        ),
    )


async def resolve_create_ticket(info: Info, data: TicketCreateInput) -> TicketType:
    user = await require_permission(info, Permissions.TICKET_CREATE)
    usecase = CreateTicketUseCase(info.context.uow)
    res = await usecase.execute(
        TicketApiMapper.to_create_ticket_dto(
            TicketCreateRequest(title=data.title, body=data.body),
            user.safe_id,
        )
    )
    mapped = TicketApiMapper.from_create_ticket_dto(res)
    return ticket_from_mapping(mapped.model_dump())


async def resolve_ticket(info: Info, ticket_id: UUID) -> TicketType:
    user = await require_permission(info, Permissions.TICKET_READ)
    can_manage = await _can_manage(info, user.safe_id)
    usecase = GetTicketUseCase(info.context.uow)
    res = await usecase.execute(
        TicketApiMapper.to_get_ticket_dto(ticket_id, user.safe_id, can_manage)
    )
    mapped = TicketApiMapper.from_get_ticket_dto(res)
    return ticket_from_mapping(mapped.model_dump())


async def resolve_tickets(
    info: Info, data: TicketListInput | None = None
) -> TicketPage:
    user = await require_permission(info, Permissions.TICKET_READ)
    can_manage = await _can_manage(info, user.safe_id)
    usecase = GetTicketListByFilterUseCase(info.context.uow)
    res = await usecase.execute(
        TicketApiMapper.to_list_ticket_dto(
            _ticket_list_request(data), user.safe_id, can_manage
        )
    )
    mapped = TicketApiMapper.from_list_ticket_dto(res)
    return TicketPage(
        items=[ticket_summary_from_mapping(item.model_dump()) for item in mapped.items],
        total=mapped.total,
        page=mapped.page,
        page_size=mapped.page_size,
    )


async def resolve_add_ticket_message(
    info: Info, ticket_id: UUID, data: TicketMessageCreateInput
) -> TicketMessageType:
    user = await require_permission(info, Permissions.TICKET_REPLY)
    can_manage = await _can_manage(info, user.safe_id)
    usecase = AddTicketMessageUseCase(info.context.uow)
    res = await usecase.execute(
        TicketApiMapper.to_add_message_dto(
            ticket_id,
            TicketMessageCreateRequest(body=data.body),
            user.safe_id,
            can_manage,
        )
    )
    mapped = TicketApiMapper.from_add_message_dto(res)
    return ticket_message_from_mapping(mapped.model_dump())


async def resolve_update_ticket_status(
    info: Info, ticket_id: UUID, data: TicketUpdateStatusInput
) -> TicketSummaryType:
    await require_permission(info, Permissions.TICKET_MANAGE)
    usecase = UpdateTicketStatusUseCase(info.context.uow)
    res = await usecase.execute(
        TicketApiMapper.to_update_status_dto(
            ticket_id,
            TicketUpdateStatusRequest(status=to_domain_ticket_status(data.status)),
        )
    )
    mapped = TicketApiMapper.from_update_status_dto(res)
    return ticket_summary_from_mapping(mapped.model_dump())
