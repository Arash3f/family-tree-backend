from datetime import date

import pytest
from family_tree_graphql_client import FamilyTreeGraphQLClient
from family_tree_graphql_client.input_types import DivorceInput, MarriageCreateInput

from app.domain.entities.person import Gender, Person
from tests.e2e.graphql.graphql_auth import admin_gql_client as admin_gql_client


@pytest.mark.asyncio
async def test_graphql_marriage_crud_and_divorce(
    tree_id,
    admin_gql_client: FamilyTreeGraphQLClient,
    uow,
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

    created = await admin_gql_client.create_marriage(
        tree_id=tree_id,
        data=MarriageCreateInput(
            spouse_a_id=husband.safe_id,
            spouse_b_id=wife.safe_id,
            married_at="2020-01-01",
        ),
    )
    marriage_id = created.create_marriage.id

    fetched = await admin_gql_client.get_marriage(
        tree_id=tree_id, marriage_id=marriage_id
    )
    assert fetched.marriage.id == marriage_id

    divorced = await admin_gql_client.divorce(
        tree_id=tree_id,
        data=DivorceInput(marriage_id=marriage_id, divorced_at="2021-06-01"),
    )
    assert divorced.divorce.result

    listed = await admin_gql_client.list_marriages(tree_id=tree_id)
    assert listed.marriages.total >= 1

    deleted = await admin_gql_client.delete_marriage(
        tree_id=tree_id, marriage_id=marriage_id
    )
    assert deleted.delete_marriage.result
