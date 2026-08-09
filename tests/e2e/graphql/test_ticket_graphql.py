import pytest

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.domain.shared.permissions import Permissions
from app.infrastructure.services.security.password_hasher_impl import (
    Argon2PasswordHasher,
)
from tests.e2e.auth_headers import admin_headers as admin_headers

GRAPHQL_URL = "/graphql"


async def gql(client, query: str, variables: dict | None = None, headers=None):
    payload: dict[str, object] = {"query": query}
    if variables is not None:
        payload["variables"] = variables
    return await client.post(GRAPHQL_URL, json=payload, headers=headers or {})


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
async def test_graphql_ticket_flow(client, admin_headers, uow):  # noqa: F811
    await _create_user_with_ticket_perms(
        uow,
        username="gql_ticket_owner",
        password="gql_ticket_owner",
        permission_names=[
            Permissions.TICKET_CREATE,
            Permissions.TICKET_READ,
            Permissions.TICKET_REPLY,
        ],
    )
    owner_headers = await _login(client, "gql_ticket_owner", "gql_ticket_owner")

    create = await gql(
        client,
        """
        mutation ($data: TicketCreateInput!) {
          createTicket(data: $data) {
            id
            title
            status
            messages { body }
          }
        }
        """,
        {"data": {"title": "GraphQL help", "body": "First body"}},
        headers=owner_headers,
    )
    assert "errors" not in create.json(), create.json()
    ticket = create.json()["data"]["createTicket"]
    ticket_id = ticket["id"]
    assert ticket["title"] == "GraphQL help"
    assert ticket["status"] == "OPEN"
    assert len(ticket["messages"]) == 1

    listed = await gql(
        client,
        """
        query {
          tickets {
            total
            items { id title status }
          }
        }
        """,
        headers=owner_headers,
    )
    assert "errors" not in listed.json(), listed.json()
    assert listed.json()["data"]["tickets"]["total"] == 1

    detail = await gql(
        client,
        """
        query ($id: UUID!) {
          ticket(ticketId: $id) {
            id
            title
            messages { body authorUserId }
          }
        }
        """,
        {"id": ticket_id},
        headers=owner_headers,
    )
    assert "errors" not in detail.json(), detail.json()
    assert detail.json()["data"]["ticket"]["id"] == ticket_id

    reply = await gql(
        client,
        """
        mutation ($id: UUID!, $data: TicketMessageCreateInput!) {
          addTicketMessage(ticketId: $id, data: $data) { id body }
        }
        """,
        {"id": ticket_id, "data": {"body": "Follow up"}},
        headers=owner_headers,
    )
    assert "errors" not in reply.json(), reply.json()

    status = await gql(
        client,
        """
        mutation ($id: UUID!, $data: TicketUpdateStatusInput!) {
          updateTicketStatus(ticketId: $id, data: $data) { id status }
        }
        """,
        {"id": ticket_id, "data": {"status": "IN_PROGRESS"}},
        headers=admin_headers,
    )
    assert "errors" not in status.json(), status.json()
    assert status.json()["data"]["updateTicketStatus"]["status"] == "IN_PROGRESS"
