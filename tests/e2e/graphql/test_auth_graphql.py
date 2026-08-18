import pytest

from app.core.config import settings
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
async def test_graphql_login_success(client):
    resp = await gql(
        client,
        """
        mutation Login($username: String!, $password: String!) {
          login(username: $username, password: $password) {
            accessToken
            refreshToken
            tokenType
          }
        }
        """,
        {
            "username": settings.ADMIN_USERNAME,
            "password": settings.ADMIN_PASSWORD,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "errors" not in body
    data = body["data"]["login"]
    assert data["accessToken"]
    assert data["refreshToken"]
    assert data["tokenType"] == "bearer"


@pytest.mark.asyncio
async def test_graphql_login_invalid_credentials(client):
    resp = await gql(
        client,
        f"""
        mutation {{
          login(username: "{settings.ADMIN_USERNAME}", password: "wrong-password") {{
            accessToken
          }}
        }}
        """,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("errors")
    extensions = body["errors"][0].get("extensions") or {}
    assert extensions.get("status") in (401, 422, 400)


@pytest.mark.asyncio
async def test_graphql_me_requires_auth(client):
    resp = await gql(client, "{ me { username } }")
    assert resp.status_code == 200
    assert resp.json().get("errors")


@pytest.mark.asyncio
async def test_graphql_me_success(client, admin_headers):  # noqa: F811
    resp = await gql(client, "{ me { username roleId } }", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "errors" not in body
    assert body["data"]["me"]["username"] == settings.ADMIN_USERNAME


@pytest.mark.asyncio
async def test_graphql_refresh_and_logout(client):
    login = await gql(
        client,
        f"""
        mutation {{
          login(
            username: "{settings.ADMIN_USERNAME}"
            password: "{settings.ADMIN_PASSWORD}"
          ) {{
            accessToken
            refreshToken
          }}
        }}
        """,
    )
    tokens = login.json()["data"]["login"]

    refreshed = await gql(
        client,
        """
        mutation Refresh($token: String!) {
          refreshToken(refreshToken: $token) {
            accessToken
            refreshToken
          }
        }
        """,
        {"token": tokens["refreshToken"]},
    )
    assert "errors" not in refreshed.json()
    new_tokens = refreshed.json()["data"]["refreshToken"]
    assert new_tokens["refreshToken"] != tokens["refreshToken"]

    headers = {"Authorization": f"Bearer {new_tokens['accessToken']}"}
    logout = await gql(client, "mutation { logout { result } }", headers=headers)
    assert "errors" not in logout.json()
    assert logout.json()["data"]["logout"]["result"]

    me_after = await gql(client, "{ me { username } }", headers=headers)
    assert me_after.json().get("errors")


@pytest.mark.asyncio
async def test_graphql_member_can_login(client, member_headers):  # noqa: F811
    assert "Authorization" in member_headers
