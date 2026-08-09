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
mutation CreatePerson($treeId: UUID!, $data: PersonCreateInput!) {
  createPerson(treeId: $treeId, data: $data) {
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
async def test_graphql_create_person_permission_denied(
    client, tree_id, member_headers  # noqa: F811
):
    resp = await gql(
        client,
        CREATE_PERSON,
        {
            "treeId": str(tree_id),
            "data": {"name": "limited-person", "gender": "MALE"},
        },
        headers=member_headers,
    )
    assert resp.status_code == 200
    errors = resp.json()["errors"]
    assert errors[0]["extensions"]["error_code"] == int(ErrorCode.PERMISSION_DENIED)
    assert errors[0]["extensions"]["status"] == 403


@pytest.mark.asyncio
async def test_graphql_create_person_unauthenticated(client, tree_id):
    resp = await gql(
        client,
        CREATE_PERSON,
        {
            "treeId": str(tree_id),
            "data": {"name": "limited-person", "gender": "MALE"},
        },
    )
    assert resp.status_code == 200
    assert resp.json().get("errors")


@pytest.mark.asyncio
async def test_graphql_create_get_list_update_delete_person(
    client,
    tree_id,
    admin_headers,  # noqa: F811
    uow,  # noqa: F811
):
    father = await uow.persons.create(
        Person(
            id=None,
            tree_id=uow.tree_id,
            name="father",
            gender=Gender.MALE,
            birth_date=date(1970, 1, 1),
        )
    )
    mother = await uow.persons.create(
        Person(
            id=None,
            tree_id=uow.tree_id,
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
            "treeId": str(tree_id),
            "data": {
                "name": "child",
                "gender": "MALE",
                "parents": [
                    {"parentId": str(father.safe_id), "relationshipType": "BIOLOGICAL"},
                    {"parentId": str(mother.safe_id), "relationshipType": "BIOLOGICAL"},
                ],
            },
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
        query ($treeId: UUID!, $id: UUID!) {
          person(treeId: $treeId, personId: $id) { id name gender }
        }
        """,
        {"treeId": str(tree_id), "id": person_id},
        headers=admin_headers,
    )
    assert "errors" not in get_one.json()
    assert get_one.json()["data"]["person"]["name"] == "child"

    listed = await gql(
        client,
        """
        query ($treeId: UUID!) {
          persons(treeId: $treeId, data: { filters: { name: "child" } }) {
            total
            items { id name }
          }
        }
        """,
        {"treeId": str(tree_id)},
        headers=admin_headers,
    )
    assert "errors" not in listed.json()
    page = listed.json()["data"]["persons"]
    assert page["total"] >= 1
    assert any(item["id"] == person_id for item in page["items"])

    updated = await gql(
        client,
        """
        mutation ($treeId: UUID!, $data: PersonUpdateInput!) {
          updatePerson(treeId: $treeId, data: $data) { id name }
        }
        """,
        {
            "treeId": str(tree_id),
            "data": {
                "data": {"name": "child-updated"},
                "where": {"personId": person_id},
            },
        },
        headers=admin_headers,
    )
    assert "errors" not in updated.json()
    assert updated.json()["data"]["updatePerson"]["name"] == "child-updated"

    deleted = await gql(
        client,
        """
        mutation ($treeId: UUID!, $id: UUID!) {
          deletePerson(treeId: $treeId, personId: $id) { result }
        }
        """,
        {"treeId": str(tree_id), "id": person_id},
        headers=admin_headers,
    )
    assert "errors" not in deleted.json()
    assert deleted.json()["data"]["deletePerson"]["result"]
