from uuid import UUID

from fastapi import APIRouter, Depends

from app.application.services.authorization_service import AuthorizationService
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
from app.presentation.dependencies import (
    get_authorization_service_request,
    get_request_uow,
)
from app.presentation.rest.dependencies.auth_dependencies import get_current_user
from app.presentation.rest.dependencies.permission_guard import RequirePermission
from app.presentation.rest.schemas.dto.common import PaginatedResponse
from app.presentation.rest.schemas.dto.ticket_schema import (
    FilterTicketRequest,
    TicketCreateRequest,
    TicketCreateResponse,
    TicketGetResponse,
    TicketMessageCreateRequest,
    TicketMessageCreateResponse,
    TicketSummaryModel,
    TicketUpdateStatusRequest,
    TicketUpdateStatusResponse,
)
from app.presentation.rest.schemas.mappers.ticket_mappers import TicketApiMapper

router = APIRouter(prefix="/tickets", tags=["Tickets"])


async def _user_can_manage(user_id: UUID, auth_service: AuthorizationService) -> bool:
    return await auth_service.user_has_permission(user_id, Permissions.TICKET_REPLY)


@router.post(
    "",
    response_model=TicketCreateResponse,
    dependencies=[Depends(RequirePermission(Permissions.TICKET_CREATE))],
    status_code=201,
)
async def create_ticket(
    data: TicketCreateRequest,
    current_user=Depends(get_current_user),
    uow=Depends(get_request_uow),
) -> TicketCreateResponse:
    usecase = CreateTicketUseCase(uow)
    res = await usecase.execute(
        TicketApiMapper.to_create_ticket_dto(data, current_user.safe_id)
    )
    return TicketApiMapper.from_create_ticket_dto(res)


@router.post(
    "/list",
    response_model=PaginatedResponse[TicketSummaryModel],
)
async def list_tickets(
    data: FilterTicketRequest,
    current_user=Depends(get_current_user),
    uow=Depends(get_request_uow),
    auth_service: AuthorizationService = Depends(get_authorization_service_request),
) -> PaginatedResponse[TicketSummaryModel]:
    can_manage = await _user_can_manage(current_user.safe_id, auth_service)
    usecase = GetTicketListByFilterUseCase(uow)
    res = await usecase.execute(
        TicketApiMapper.to_list_ticket_dto(data, current_user.safe_id, can_manage)
    )
    return TicketApiMapper.from_list_ticket_dto(res)


@router.get(
    "/{ticket_id}",
    response_model=TicketGetResponse,
)
async def get_ticket(
    ticket_id: UUID,
    current_user=Depends(get_current_user),
    uow=Depends(get_request_uow),
    auth_service: AuthorizationService = Depends(get_authorization_service_request),
) -> TicketGetResponse:
    can_manage = await _user_can_manage(current_user.safe_id, auth_service)
    usecase = GetTicketUseCase(uow)
    res = await usecase.execute(
        TicketApiMapper.to_get_ticket_dto(ticket_id, current_user.safe_id, can_manage)
    )
    return TicketApiMapper.from_get_ticket_dto(res)


@router.post(
    "/{ticket_id}/messages",
    response_model=TicketMessageCreateResponse,
    status_code=201,
)
async def add_ticket_message(
    ticket_id: UUID,
    data: TicketMessageCreateRequest,
    current_user=Depends(get_current_user),
    uow=Depends(get_request_uow),
    auth_service: AuthorizationService = Depends(get_authorization_service_request),
) -> TicketMessageCreateResponse:
    can_manage = await _user_can_manage(current_user.safe_id, auth_service)
    usecase = AddTicketMessageUseCase(uow)
    res = await usecase.execute(
        TicketApiMapper.to_add_message_dto(
            ticket_id, data, current_user.safe_id, can_manage
        )
    )
    return TicketApiMapper.from_add_message_dto(res)


@router.patch(
    "/{ticket_id}/status",
    response_model=TicketUpdateStatusResponse,
)
async def update_ticket_status(
    ticket_id: UUID,
    data: TicketUpdateStatusRequest,
    current_user=Depends(get_current_user),
    uow=Depends(get_request_uow),
    auth_service: AuthorizationService = Depends(get_authorization_service_request),
) -> TicketUpdateStatusResponse:
    can_manage = await _user_can_manage(current_user.safe_id, auth_service)
    usecase = UpdateTicketStatusUseCase(uow)
    res = await usecase.execute(
        TicketApiMapper.to_update_status_dto(
            ticket_id, data, current_user.safe_id, can_manage
        )
    )
    return TicketApiMapper.from_update_status_dto(res)
