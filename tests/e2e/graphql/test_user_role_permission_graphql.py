import pytest

from tests.e2e.auth_headers import admin_headers as admin_headers
from tests.e2e.auth_headers import member_headers as member_headers

GRAPHQL_URL = "/graphql"


async def gql(
    client,
    query: str,
    variables: dict | None = None,
    headers: dict | None = None,
):
    payload: dict[str, object] = {"query": query}
    if variables is not None:
        payload["variables"] = variables
    return await client.post(GRAPHQL_URL, json=payload, headers=headers or {})


@pytest.mark.asyncio
async def test_graphql_users_roles_permissions_flow(client, admin_headers):  # noqa: F811
    permissions = await gql(
        client,
        """
        query {
          permissions {
            total
            items { id name }
          }
        }
        """,
        headers=admin_headers,
    )
    assert "errors" not in permissions.json(), permissions.json()
    perm_page = permissions.json()["data"]["permissions"]
    assert perm_page["total"] >= 1
    permission_ids = [item["id"] for item in perm_page["items"][:3]]

    role = await gql(
        client,
        """
        mutation ($data: RoleCreateInput!) {
          createRole(data: $data) { id name permissionIds }
        }
        """,
        {"data": {"name": "gql-role", "permissionIds": permission_ids}},
        headers=admin_headers,
    )
    assert "errors" not in role.json(), role.json()
    role_id = role.json()["data"]["createRole"]["id"]

    user = await gql(
        client,
        """
        mutation ($data: UserCreateInput!) {
          createUser(data: $data) { id username fullname roleId }
        }
        """,
        {
            "data": {
                "username": "gql_user",
                "fullname": "GQL User",
                "password": "Secret123!",
                "rePassword": "Secret123!",
                "roleId": role_id,
            }
        },
        headers=admin_headers,
    )
    assert "errors" not in user.json(), user.json()
    user_id = user.json()["data"]["createUser"]["id"]

    get_user = await gql(
        client,
        """
        query ($id: UUID!) {
          user(userId: $id) { id username roleId }
        }
        """,
        {"id": user_id},
        headers=admin_headers,
    )
    assert "errors" not in get_user.json()
    assert get_user.json()["data"]["user"]["username"] == "gql_user"

    get_role = await gql(
        client,
        """
        query ($id: UUID!) {
          role(roleId: $id) { id name }
        }
        """,
        {"id": role_id},
        headers=admin_headers,
    )
    assert "errors" not in get_role.json()

    users = await gql(
        client,
        """
        query {
          users(data: { filters: { username: "gql_user" } }) {
            total
            items { id username }
          }
        }
        """,
        headers=admin_headers,
    )
    assert "errors" not in users.json()
    assert users.json()["data"]["users"]["total"] >= 1

    deleted_user = await gql(
        client,
        """
        mutation ($id: UUID!) {
          deleteUser(userId: $id) { result }
        }
        """,
        {"id": user_id},
        headers=admin_headers,
    )
    assert "errors" not in deleted_user.json()

    deleted_role = await gql(
        client,
        """
        mutation ($id: UUID!) {
          deleteRole(roleId: $id) { result }
        }
        """,
        {"id": role_id},
        headers=admin_headers,
    )
    assert "errors" not in deleted_role.json()


@pytest.mark.asyncio
async def test_graphql_permissions_denied_for_member(client, member_headers):  # noqa: F811
    resp = await gql(
        client,
        "{ permissions { total } }",
        headers=member_headers,
    )
    assert resp.json().get("errors")
