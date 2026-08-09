from datetime import date

import pytest

from app.domain.entities.person import Gender, Person
from app.utils.error_codes import ErrorCode
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


CREATE_PERSON = """
mutation CreatePerson($data: PersonCreateInput!) {
  createPerson(data: $data) {
    id
    name
    gender
    parents {
      parentId
      relationshipType
    }
  }
}
"""


@pytest.mark.asyncio
async def test_graphql_create_person_permission_denied(client, member_headers):  # noqa: F811
    resp = await gql(
        client,
        CREATE_PERSON,
        {"data": {"name": "limited-person", "gender": "MALE"}},
        headers=member_headers,
    )
    assert resp.status_code == 200
    errors = resp.json()["errors"]
    assert errors[0]["extensions"]["error_code"] == int(ErrorCode.PERMISSION_DENIED)
    assert errors[0]["extensions"]["status"] == 403


@pytest.mark.asyncio
async def test_graphql_create_person_unauthenticated(client):
    resp = await gql(
        client,
        CREATE_PERSON,
        {"data": {"name": "limited-person", "gender": "MALE"}},
    )
    assert resp.status_code == 200
    assert resp.json().get("errors")


@pytest.mark.asyncio
async def test_graphql_create_get_list_update_delete_person(
    client,
    admin_headers,  # noqa: F811
    uow,  # noqa: F811
):
    father = await uow.persons.create(
        Person(
            id=None,
            name="father",
            gender=Gender.MALE,
            birth_date=date(1970, 1, 1),
        )
    )
    mother = await uow.persons.create(
        Person(
            id=None,
            name="mother",
            gender=Gender.FEMALE,
            birth_date=date(1972, 1, 1),
        )
    )
    await uow.commit()

    create = await gql(
        client,
        CREATE_PERSON,
        {
            "data": {
                "name": "child",
                "gender": "MALE",
                "parents": [
                    {"parentId": str(father.safe_id), "relationshipType": "BIOLOGICAL"},
                    {"parentId": str(mother.safe_id), "relationshipType": "BIOLOGICAL"},
                ],
            }
        },
        headers=admin_headers,
    )
    assert "errors" not in create.json(), create.json()
    person = create.json()["data"]["createPerson"]
    person_id = person["id"]
    assert person["name"] == "child"
    assert {p["parentId"] for p in person["parents"]} == {
        str(father.safe_id),
        str(mother.safe_id),
    }

    get_one = await gql(
        client,
        """
        query ($id: UUID!) {
          person(personId: $id) { id name gender }
        }
        """,
        {"id": person_id},
        headers=admin_headers,
    )
    assert "errors" not in get_one.json()
    assert get_one.json()["data"]["person"]["name"] == "child"

    listed = await gql(
        client,
        """
        query {
          persons(data: { filters: { name: "child" } }) {
            total
            items { id name }
          }
        }
        """,
        headers=admin_headers,
    )
    assert "errors" not in listed.json()
    page = listed.json()["data"]["persons"]
    assert page["total"] >= 1
    assert any(item["id"] == person_id for item in page["items"])

    updated = await gql(
        client,
        """
        mutation ($data: PersonUpdateInput!) {
          updatePerson(data: $data) { id name }
        }
        """,
        {
            "data": {
                "data": {"name": "child-updated"},
                "where": {"personId": person_id},
            }
        },
        headers=admin_headers,
    )
    assert "errors" not in updated.json()
    assert updated.json()["data"]["updatePerson"]["name"] == "child-updated"

    deleted = await gql(
        client,
        """
        mutation ($id: UUID!) {
          deletePerson(personId: $id) { result }
        }
        """,
        {"id": person_id},
        headers=admin_headers,
    )
    assert "errors" not in deleted.json()
    assert deleted.json()["data"]["deletePerson"]["result"]
