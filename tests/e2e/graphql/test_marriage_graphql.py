from datetime import date

import pytest

from app.domain.entities.person import Gender, Person
from tests.e2e.auth_headers import admin_headers as admin_headers

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
async def test_graphql_marriage_crud_and_divorce(client, admin_headers, uow):  # noqa: F811
    husband = await uow.persons.create(
        Person(id=None, name="h", gender=Gender.MALE, birth_date=date(1990, 1, 1))
    )
    wife = await uow.persons.create(
        Person(id=None, name="w", gender=Gender.FEMALE, birth_date=date(1992, 1, 1))
    )
    await uow.commit()

    create = await gql(
        client,
        """
        mutation ($data: MarriageCreateInput!) {
          createMarriage(data: $data) {
            id spouseAId spouseBId marriedAt divorcedAt
          }
        }
        """,
        {
            "data": {
                "spouseAId": str(husband.safe_id),
                "spouseBId": str(wife.safe_id),
                "marriedAt": "2020-01-01",
            }
        },
        headers=admin_headers,
    )
    assert "errors" not in create.json(), create.json()
    marriage = create.json()["data"]["createMarriage"]
    marriage_id = marriage["id"]

    get_one = await gql(
        client,
        """
        query ($id: UUID!) {
          marriage(marriageId: $id) { id spouseAId spouseBId }
        }
        """,
        {"id": marriage_id},
        headers=admin_headers,
    )
    assert "errors" not in get_one.json()

    divorce = await gql(
        client,
        """
        mutation ($data: DivorceInput!) {
          divorce(data: $data) { result }
        }
        """,
        {"data": {"marriageId": marriage_id, "divorcedAt": "2021-06-01"}},
        headers=admin_headers,
    )
    assert "errors" not in divorce.json(), divorce.json()

    listed = await gql(
        client,
        """
        query {
          marriages {
            total
            items { id }
          }
        }
        """,
        headers=admin_headers,
    )
    assert "errors" not in listed.json()
    assert listed.json()["data"]["marriages"]["total"] >= 1

    deleted = await gql(
        client,
        """
        mutation ($id: UUID!) {
          deleteMarriage(marriageId: $id) { result }
        }
        """,
        {"id": marriage_id},
        headers=admin_headers,
    )
    assert "errors" not in deleted.json()
