import pytest
from family_tree_graphql_client import FamilyTreeGraphQLClient
from family_tree_graphql_client.enums import TicketCategory, TicketStatus
from family_tree_graphql_client.input_types import (
    TicketCreateInput,
    TicketMessageCreateInput,
    TicketUpdateStatusInput,
)

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.domain.shared.permissions import Permissions
from app.infrastructure.services.security.password_hasher_impl import (
    Argon2PasswordHasher,
)
from tests.e2e.graphql.graphql_auth import admin_gql_client as admin_gql_client
from tests.e2e.graphql.graphql_auth import gql_client_with_headers


async def _login_headers(client, username: str, password: str) -> dict[str, str]:
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
async def test_graphql_ticket_flow(
    admin_gql_client: FamilyTreeGraphQLClient, client, uow, asgi_transport
):
    await _create_user_with_ticket_perms(
        uow,
        username="gql_ticket_owner",
        password="gql_ticket_owner",
        permission_names=[
            Permissions.TICKET_CREATE,
            Permissions.TICKET_READ,
        ],
    )
    owner_headers = await _login_headers(client, "gql_ticket_owner", "gql_ticket_owner")
    owner_client = gql_client_with_headers(asgi_transport, owner_headers)

    created = await owner_client.create_ticket(
        data=TicketCreateInput(
            title="GraphQL help", body="First body", category=TicketCategory.GENERAL
        )
    )
    ticket = created.create_ticket
    ticket_id = ticket.id
    assert ticket.title == "GraphQL help"
    assert ticket.status == TicketStatus.OPEN
    assert len(ticket.messages) == 1

    listed = await owner_client.list_tickets()
    assert listed.tickets.total == 1

    detail = await owner_client.get_ticket(id=ticket_id)
    assert detail.ticket.id == ticket_id

    reply = await owner_client.add_ticket_message(
        id=ticket_id, data=TicketMessageCreateInput(body="Follow up")
    )
    assert reply.add_ticket_message.body == "Follow up"

    status = await admin_gql_client.update_ticket_status(
        id=ticket_id,
        data=TicketUpdateStatusInput(status=TicketStatus.IN_PROGRESS),
    )
    assert status.update_ticket_status.status == TicketStatus.IN_PROGRESS
