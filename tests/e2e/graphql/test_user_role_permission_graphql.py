import pytest
from family_tree_graphql_client import FamilyTreeGraphQLClient
from family_tree_graphql_client.exceptions import GraphQLClientGraphQLMultiError
from family_tree_graphql_client.input_types import (
    RoleCreateInput,
    UserCreateInput,
    UserFilterInput,
    UserListInput,
)

from tests.e2e.graphql.graphql_auth import admin_gql_client as admin_gql_client
from tests.e2e.graphql.graphql_auth import member_gql_client as member_gql_client


@pytest.mark.asyncio
async def test_graphql_users_roles_permissions_flow(
    admin_gql_client: FamilyTreeGraphQLClient,
):
    permissions = await admin_gql_client.list_permissions()
    perm_page = permissions.permissions
    assert perm_page.total >= 1
    permission_ids = [item.id for item in perm_page.items[:3]]

    role = await admin_gql_client.create_role(
        data=RoleCreateInput(name="gql-role", permission_ids=permission_ids)
    )
    role_id = role.create_role.id

    user = await admin_gql_client.create_user(
        data=UserCreateInput(
            username="gql_user",
            fullname="GQL User",
            password="Secret123!",
            re_password="Secret123!",
            role_id=role_id,
        )
    )
    user_id = user.create_user.id

    get_user = await admin_gql_client.get_user(id=user_id)
    assert get_user.user.username == "gql_user"

    get_role = await admin_gql_client.get_role(id=role_id)
    assert get_role.role.id == role_id

    users = await admin_gql_client.list_users(
        data=UserListInput(filters=UserFilterInput(username="gql_user"))
    )
    assert users.users.total >= 1

    deleted_user = await admin_gql_client.delete_user(id=user_id)
    assert deleted_user.delete_user.result

    deleted_role = await admin_gql_client.delete_role(id=role_id)
    assert deleted_role.delete_role.result


@pytest.mark.asyncio
async def test_graphql_permissions_denied_for_member(
    member_gql_client: FamilyTreeGraphQLClient,
):
    with pytest.raises(GraphQLClientGraphQLMultiError):
        await member_gql_client.list_permissions()
