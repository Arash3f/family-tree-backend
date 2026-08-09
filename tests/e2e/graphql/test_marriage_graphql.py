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
async def test_graphql_marriage_crud_and_divorce(
    client,
    tree_id,
    admin_headers,
    uow,  # noqa: F811
):
    husband = await uow.persons.create(
        Person(
            id=None,
            tree_id=uow.tree_id,
            name="h",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
        )
    )
    wife = await uow.persons.create(
        Person(
            id=None,
            tree_id=uow.tree_id,
            name="w",
            gender=Gender.FEMALE,
            birth_date=date(1992, 1, 1),
        )
    )
    await uow.commit()

    create = await gql(
        client,
        """
        mutation ($treeId: UUID!, $data: MarriageCreateInput!) {
          createMarriage(treeId: $treeId, data: $data) {
            id spouseAId spouseBId marriedAt divorcedAt
          }
        }
        """,
        {
            "treeId": str(tree_id),
            "data": {
                "spouseAId": str(husband.safe_id),
                "spouseBId": str(wife.safe_id),
                "marriedAt": "2020-01-01",
            },
        },
        headers=admin_headers,
    )
    assert "errors" not in create.json(), create.json()
    marriage = create.json()["data"]["createMarriage"]
    marriage_id = marriage["id"]

    get_one = await gql(
        client,
        """
        query ($treeId: UUID!, $id: UUID!) {
          marriage(treeId: $treeId, marriageId: $id) { id spouseAId spouseBId }
        }
        """,
        {"treeId": str(tree_id), "id": marriage_id},
        headers=admin_headers,
    )
    assert "errors" not in get_one.json()

    divorce = await gql(
        client,
        """
        mutation ($treeId: UUID!, $data: DivorceInput!) {
          divorce(treeId: $treeId, data: $data) { result }
        }
        """,
        {
            "treeId": str(tree_id),
            "data": {"marriageId": marriage_id, "divorcedAt": "2021-06-01"},
        },
        headers=admin_headers,
    )
    assert "errors" not in divorce.json(), divorce.json()

    listed = await gql(
        client,
        """
        query ($treeId: UUID!) {
          marriages(treeId: $treeId) {
            total
            items { id }
          }
        }
        """,
        {"treeId": str(tree_id)},
        headers=admin_headers,
    )
    assert "errors" not in listed.json()
    assert listed.json()["data"]["marriages"]["total"] >= 1

    deleted = await gql(
        client,
        """
        mutation ($treeId: UUID!, $id: UUID!) {
          deleteMarriage(treeId: $treeId, marriageId: $id) { result }
        }
        """,
        {"treeId": str(tree_id), "id": marriage_id},
        headers=admin_headers,
    )
    assert "errors" not in deleted.json()
