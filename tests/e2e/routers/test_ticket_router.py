import json

import pytest
from family_tree_api_client import AuthenticatedClient, Client
from family_tree_api_client.api.auth.login_auth_login_post import (
    asyncio_detailed as login,
)
from family_tree_api_client.api.tickets.add_ticket_message_tickets_ticket_id_messages_post import (  # noqa: E501
    asyncio_detailed as add_ticket_message,
)
from family_tree_api_client.api.tickets.create_ticket_tickets_post import (
    asyncio_detailed as create_ticket,
)
from family_tree_api_client.api.tickets.get_ticket_tickets_ticket_id_get import (
    asyncio_detailed as get_ticket,
)
from family_tree_api_client.api.tickets.list_tickets_tickets_list_post import (
    asyncio_detailed as list_tickets,
)
from family_tree_api_client.api.tickets.update_ticket_status_tickets_ticket_id_status_patch import (  # noqa: E501
    asyncio_detailed as update_ticket_status,
)
from family_tree_api_client.models.body_login_auth_login_post import (
    BodyLoginAuthLoginPost,
)
from family_tree_api_client.models.filter_ticket_request import FilterTicketRequest
from family_tree_api_client.models.login_response import LoginResponse
from family_tree_api_client.models.ticket_category import TicketCategory
from family_tree_api_client.models.ticket_create_request import TicketCreateRequest
from family_tree_api_client.models.ticket_create_response import TicketCreateResponse
from family_tree_api_client.models.ticket_get_response import TicketGetResponse
from family_tree_api_client.models.ticket_message_create_request import (
    TicketMessageCreateRequest,
)
from family_tree_api_client.models.ticket_message_create_response import (
    TicketMessageCreateResponse,
)
from family_tree_api_client.models.ticket_status import TicketStatus
from family_tree_api_client.models.ticket_update_status_request import (
    TicketUpdateStatusRequest,
)
from family_tree_api_client.models.ticket_update_status_response import (
    TicketUpdateStatusResponse,
)
from httpx import ASGITransport, AsyncClient

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.domain.shared.permissions import Permissions
from app.infrastructure.services.security.password_hasher_impl import (
    Argon2PasswordHasher,
)
from app.utils.error_codes import ERROR_MESSAGES, ErrorCode
from tests.e2e.auth_headers import admin_client as admin_client
from tests.e2e.auth_headers import member_client as member_client


async def _login(
    client: Client, asgi_transport: ASGITransport, username: str, password: str
) -> AuthenticatedClient:
    resp = await login(
        client=client,
        body=BodyLoginAuthLoginPost(username=username, password=password),
    )
    assert resp.status_code == 200, resp.content
    assert isinstance(resp.parsed, LoginResponse)
    token = resp.parsed.access_token

    async_httpx = AsyncClient(
        transport=asgi_transport,
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {token}"},
    )
    authenticated = AuthenticatedClient(base_url="http://testserver", token=token)
    authenticated.set_async_httpx_client(async_httpx)
    return authenticated


async def _create_user_with_ticket_perms(
    uow, *, username: str, password: str, permission_names: list[str]
) -> User:
    permission_ids = []
    for name in permission_names:
        existing = await uow.permissions.get_by_name(name)
        if existing:
            permission_ids.append(existing.safe_id)
        else:
            created = await uow.permissions.create(Permission(name=name))
            permission_ids.append(created.safe_id)

    role = await uow.roles.create(
        Role(name=f"role_{username}", permission_ids=permission_ids)
    )
    hasher = Argon2PasswordHasher()
    user = await uow.users.create(
        User(
            username=username,
            password_hash=hasher.hash(password),
            role_id=role.safe_id,
        )
    )
    await uow.commit()
    return user


@pytest.mark.asyncio
async def test_create_ticket_permission_denied(member_client: AuthenticatedClient):
    req = TicketCreateRequest(
        title="Help", body="Need support", category=TicketCategory.GENERAL
    )
    resp = await create_ticket(client=member_client, body=req)
    assert resp.status_code == 403
    assert json.loads(resp.content)["error_code"] == ErrorCode.PERMISSION_DENIED


@pytest.mark.asyncio
async def test_ticket_flow_owner_and_admin(
    client: Client, admin_client: AuthenticatedClient, uow, asgi_transport
):
    owner = await _create_user_with_ticket_perms(
        uow,
        username="ticket_owner",
        password="ticket_owner",
        permission_names=[
            Permissions.TICKET_CREATE,
            Permissions.TICKET_READ,
        ],
    )
    other = await _create_user_with_ticket_perms(
        uow,
        username="ticket_other",
        password="ticket_other",
        permission_names=[
            Permissions.TICKET_CREATE,
            Permissions.TICKET_READ,
        ],
    )
    owner_client = await _login(client, asgi_transport, "ticket_owner", "ticket_owner")
    other_client = await _login(client, asgi_transport, "ticket_other", "ticket_other")

    create_resp = await create_ticket(
        client=owner_client,
        body=TicketCreateRequest(
            title="Cannot login",
            body="I cannot login to the app",
            category=TicketCategory.ACCOUNT,
        ),
    )
    assert create_resp.status_code == 201, create_resp.content
    assert isinstance(create_resp.parsed, TicketCreateResponse)
    created = create_resp.parsed
    assert created.title == "Cannot login"
    assert created.status == TicketStatus.OPEN
    assert created.created_by_user_id == owner.safe_id
    assert created.created_by_can_manage is False
    assert len(created.messages) == 1

    ticket_id = created.id

    # other user cannot read owner's ticket
    denied = await get_ticket(ticket_id=ticket_id, client=other_client)
    assert denied.status_code == 403
    assert json.loads(denied.content)["error_code"] == ErrorCode.TICKET_ACCESS_DENIED

    # owner can read
    get_resp = await get_ticket(ticket_id=ticket_id, client=owner_client)
    assert get_resp.status_code == 200
    assert isinstance(get_resp.parsed, TicketGetResponse)
    detail = get_resp.parsed
    assert detail.id == ticket_id
    assert len(detail.messages) == 1

    # list is scoped for owner
    list_resp = await list_tickets(client=owner_client, body=FilterTicketRequest())
    assert list_resp.status_code == 200
    assert list_resp.parsed.total == 1

    other_list = await list_tickets(client=other_client, body=FilterTicketRequest())
    assert other_list.status_code == 200
    assert other_list.parsed.total == 0

    # owner reply
    msg_resp = await add_ticket_message(
        ticket_id=ticket_id,
        client=owner_client,
        body=TicketMessageCreateRequest(body="Any update?"),
    )
    assert msg_resp.status_code == 201
    assert isinstance(msg_resp.parsed, TicketMessageCreateResponse)

    # admin manage: list all + status update + reply
    admin_list = await list_tickets(client=admin_client, body=FilterTicketRequest())
    assert admin_list.status_code == 200
    assert admin_list.parsed.total >= 1

    status_resp = await update_ticket_status(
        ticket_id=ticket_id,
        client=admin_client,
        body=TicketUpdateStatusRequest(status=TicketStatus.IN_PROGRESS),
    )
    assert status_resp.status_code == 200
    assert isinstance(status_resp.parsed, TicketUpdateStatusResponse)
    updated = status_resp.parsed
    assert updated.status == TicketStatus.IN_PROGRESS

    admin_msg = await add_ticket_message(
        ticket_id=ticket_id,
        client=admin_client,
        body=TicketMessageCreateRequest(body="We are checking"),
    )
    assert admin_msg.status_code == 201

    # close and reject further replies
    close_resp = await update_ticket_status(
        ticket_id=ticket_id,
        client=admin_client,
        body=TicketUpdateStatusRequest(status=TicketStatus.CLOSED),
    )
    assert close_resp.status_code == 200

    closed_msg = await add_ticket_message(
        ticket_id=ticket_id,
        client=owner_client,
        body=TicketMessageCreateRequest(body="still open?"),
    )
    assert closed_msg.status_code == 409
    closed_body = json.loads(closed_msg.content)
    assert closed_body["error_code"] == ErrorCode.TICKET_CLOSED
    assert closed_body["message"] == ERROR_MESSAGES["en"][ErrorCode.TICKET_CLOSED]

    # silence unused variable warning for other user creation side-effect
    assert other.username == "ticket_other"


@pytest.mark.asyncio
async def test_admin_created_ticket_is_not_a_support_request(
    client: Client, admin_client: AuthenticatedClient, uow, asgi_transport
):
    manager = await _create_user_with_ticket_perms(
        uow,
        username="ticket_manager",
        password="ticket_manager",
        permission_names=[
            Permissions.TICKET_REPLY,
            Permissions.TICKET_READ,
            Permissions.TICKET_CREATE,
        ],
    )
    manager_client = await _login(
        client, asgi_transport, "ticket_manager", "ticket_manager"
    )

    create_resp = await create_ticket(
        client=admin_client,
        body=TicketCreateRequest(
            title="Internal note",
            body="Opened by support",
            category=TicketCategory.GENERAL,
        ),
    )
    assert create_resp.status_code == 201, create_resp.content
    assert isinstance(create_resp.parsed, TicketCreateResponse)
    created = create_resp.parsed
    assert created.created_by_can_manage is True

    listed = await list_tickets(client=manager_client, body=FilterTicketRequest())
    assert listed.status_code == 200
    items = listed.parsed.items
    match = next(item for item in items if item.id == created.id)
    assert match.created_by_can_manage is True
    assert manager.username == "ticket_manager"
