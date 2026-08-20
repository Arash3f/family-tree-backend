from datetime import date

import pytest
from family_tree_graphql_client import FamilyTreeGraphQLClient
from family_tree_graphql_client.enums import Gender as ApiGender
from family_tree_graphql_client.exceptions import GraphQLClientGraphQLMultiError
from family_tree_graphql_client.input_types import (
    ParentLinkInput,
    PersonCreateInput,
    PersonUpdateDataInput,
    PersonUpdateInput,
    PersonUpdateWhereInput,
)

from app.domain.entities.person import Gender, Person
from app.utils.error_codes import ErrorCode
from tests.e2e.graphql.graphql_auth import admin_gql_client as admin_gql_client
from tests.e2e.graphql.graphql_auth import gql_client as gql_client
from tests.e2e.graphql.graphql_auth import member_gql_client as member_gql_client

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_graphql_create_person_permission_denied(
    tree_id, member_gql_client: FamilyTreeGraphQLClient
):
    with pytest.raises(GraphQLClientGraphQLMultiError) as exc_info:
        await member_gql_client.create_person(
            tree_id=tree_id,
            data=PersonCreateInput(name="limited-person", gender=ApiGender.MALE),
        )

    error = exc_info.value.errors[0]
    assert error.extensions["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
    assert error.extensions["status"] == 403


@pytest.mark.asyncio
async def test_graphql_create_person_unauthenticated(
    tree_id, gql_client: FamilyTreeGraphQLClient
):
    with pytest.raises(GraphQLClientGraphQLMultiError):
        await gql_client.create_person(
            tree_id=tree_id,
            data=PersonCreateInput(name="limited-person", gender=ApiGender.MALE),
        )


@pytest.mark.asyncio
async def test_graphql_create_get_list_update_delete_person(
    tree_id,
    admin_gql_client: FamilyTreeGraphQLClient,
    uow,
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

    created = await admin_gql_client.create_person(
        tree_id=tree_id,
        data=PersonCreateInput(
            name="child",
            gender=ApiGender.MALE,
            parents=[
                ParentLinkInput(parent_id=father.safe_id),
                ParentLinkInput(parent_id=mother.safe_id),
            ],
        ),
    )
    person = created.create_person
    person_id = person.id
    assert person.name == "child"
    assert {str(p.parent_id) for p in person.parents} == {
        str(father.safe_id),
        str(mother.safe_id),
    }

    fetched = await admin_gql_client.get_person(tree_id=tree_id, person_id=person_id)
    assert fetched.person.name == "child"

    listed = await admin_gql_client.list_persons(tree_id=tree_id)
    assert listed.persons.total >= 1
    assert any(item.id == person_id for item in listed.persons.items)

    updated = await admin_gql_client.update_person(
        tree_id=tree_id,
        data=PersonUpdateInput(
            data=PersonUpdateDataInput(name="child-updated"),
            where=PersonUpdateWhereInput(person_id=person_id),
        ),
    )
    assert updated.update_person.name == "child-updated"

    deleted = await admin_gql_client.delete_person(tree_id=tree_id, person_id=person_id)
    assert deleted.delete_person.result
