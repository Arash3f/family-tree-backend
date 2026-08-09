import pytest
from pydantic import TypeAdapter

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.domain.shared.enums.ticket_status import TicketStatus
from app.domain.shared.permissions import Permissions
from app.infrastructure.services.security.password_hasher_impl import (
    Argon2PasswordHasher,
)
from app.presentation.rest.schemas.dto.ticket_schema import (
    FilterTicketRequest,
    TicketCreateRequest,
    TicketCreateResponse,
    TicketGetResponse,
    TicketMessageCreateRequest,
    TicketMessageCreateResponse,
    TicketUpdateStatusRequest,
    TicketUpdateStatusResponse,
)
from app.utils.error_codes import ERROR_MESSAGES, ErrorCode
from tests.e2e.auth_headers import admin_headers as admin_headers
from tests.e2e.auth_headers import member_headers as member_headers

BASE_URL = "/tickets"


async def _login(client, username: str, password: str) -> dict[str, str]:
    resp = await client.post(
        "/auth/login", data={"username": username, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


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
async def test_create_ticket_permission_denied(client, member_headers):  # noqa: F811
    req = TicketCreateRequest(title="Help", body="Need support")
    resp = await client.post(
        f"{BASE_URL}/",
        json=req.model_dump(mode="json"),
        headers=member_headers,
    )
    assert resp.status_code == 403
    assert resp.json()["error_code"] == ErrorCode.PERMISSION_DENIED


@pytest.mark.asyncio
async def test_ticket_flow_owner_and_admin(client, admin_headers, uow):  # noqa: F811
    owner = await _create_user_with_ticket_perms(
        uow,
        username="ticket_owner",
        password="ticket_owner",
        permission_names=[
            Permissions.TICKET_CREATE,
            Permissions.TICKET_READ,
            Permissions.TICKET_REPLY,
        ],
    )
    other = await _create_user_with_ticket_perms(
        uow,
        username="ticket_other",
        password="ticket_other",
        permission_names=[
            Permissions.TICKET_CREATE,
            Permissions.TICKET_READ,
            Permissions.TICKET_REPLY,
        ],
    )
    owner_headers = await _login(client, "ticket_owner", "ticket_owner")
    other_headers = await _login(client, "ticket_other", "ticket_other")

    create_resp = await client.post(
        f"{BASE_URL}/",
        json=TicketCreateRequest(
            title="Cannot login", body="I cannot login to the app"
        ).model_dump(mode="json"),
        headers=owner_headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    created = TypeAdapter(TicketCreateResponse).validate_python(create_resp.json())
    assert created.title == "Cannot login"
    assert created.status == TicketStatus.OPEN
    assert created.created_by_user_id == owner.safe_id
    assert len(created.messages) == 1

    ticket_id = created.id

    # other user cannot read owner's ticket
    denied = await client.get(f"{BASE_URL}/{ticket_id}", headers=other_headers)
    assert denied.status_code == 403
    assert denied.json()["error_code"] == ErrorCode.TICKET_ACCESS_DENIED

    # owner can read
    get_resp = await client.get(f"{BASE_URL}/{ticket_id}", headers=owner_headers)
    assert get_resp.status_code == 200
    detail = TypeAdapter(TicketGetResponse).validate_python(get_resp.json())
    assert detail.id == ticket_id
    assert len(detail.messages) == 1

    # list is scoped for owner
    list_resp = await client.post(
        f"{BASE_URL}/list",
        json=FilterTicketRequest().model_dump(mode="json"),
        headers=owner_headers,
    )
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    other_list = await client.post(
        f"{BASE_URL}/list",
        json=FilterTicketRequest().model_dump(mode="json"),
        headers=other_headers,
    )
    assert other_list.status_code == 200
    assert other_list.json()["total"] == 0

    # owner reply
    msg_resp = await client.post(
        f"{BASE_URL}/{ticket_id}/messages",
        json=TicketMessageCreateRequest(body="Any update?").model_dump(mode="json"),
        headers=owner_headers,
    )
    assert msg_resp.status_code == 201
    TypeAdapter(TicketMessageCreateResponse).validate_python(msg_resp.json())

    # admin manage: list all + status update + reply
    admin_list = await client.post(
        f"{BASE_URL}/list",
        json=FilterTicketRequest().model_dump(mode="json"),
        headers=admin_headers,
    )
    assert admin_list.status_code == 200
    assert admin_list.json()["total"] >= 1

    status_resp = await client.patch(
        f"{BASE_URL}/{ticket_id}/status",
        json=TicketUpdateStatusRequest(status=TicketStatus.IN_PROGRESS).model_dump(
            mode="json"
        ),
        headers=admin_headers,
    )
    assert status_resp.status_code == 200
    updated = TypeAdapter(TicketUpdateStatusResponse).validate_python(
        status_resp.json()
    )
    assert updated.status == TicketStatus.IN_PROGRESS

    admin_msg = await client.post(
        f"{BASE_URL}/{ticket_id}/messages",
        json=TicketMessageCreateRequest(body="We are checking").model_dump(mode="json"),
        headers=admin_headers,
    )
    assert admin_msg.status_code == 201

    # close and reject further replies
    close_resp = await client.patch(
        f"{BASE_URL}/{ticket_id}/status",
        json=TicketUpdateStatusRequest(status=TicketStatus.CLOSED).model_dump(
            mode="json"
        ),
        headers=admin_headers,
    )
    assert close_resp.status_code == 200

    closed_msg = await client.post(
        f"{BASE_URL}/{ticket_id}/messages",
        json=TicketMessageCreateRequest(body="still open?").model_dump(mode="json"),
        headers=owner_headers,
    )
    assert closed_msg.status_code == 409
    assert closed_msg.json()["error_code"] == ErrorCode.TICKET_CLOSED
    assert closed_msg.json()["message"] == ERROR_MESSAGES["en"][ErrorCode.TICKET_CLOSED]

    # silence unused variable warning for other user creation side-effect
    assert other.username == "ticket_other"
