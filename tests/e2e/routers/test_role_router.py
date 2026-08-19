import json
from uuid import UUID

import pytest
from family_tree_api_client import AuthenticatedClient, Client
from family_tree_api_client.api.roles.create_role_roles_post import (
    asyncio_detailed as create_role,
)
from family_tree_api_client.api.roles.delete_role_roles_role_id_delete import (
    asyncio_detailed as delete_role,
)
from family_tree_api_client.api.roles.get_role_list_by_filter_roles_list_post import (
    asyncio_detailed as get_role_list_by_filter,
)
from family_tree_api_client.api.roles.get_role_roles_role_id_get import (
    asyncio_detailed as get_role,
)
from family_tree_api_client.api.roles.update_role_roles_put import (
    asyncio_detailed as update_role,
)
from family_tree_api_client.models.filter_role_request import FilterRoleRequest
from family_tree_api_client.models.paginated_response_role_model import (
    PaginatedResponseRoleModel,
)
from family_tree_api_client.models.pagination_request_params import (
    PaginationRequestParams,
)
from family_tree_api_client.models.result_response import ResultResponse
from family_tree_api_client.models.role_create_request import RoleCreateRequest
from family_tree_api_client.models.role_create_response import RoleCreateResponse
from family_tree_api_client.models.role_filter_request_data import (
    RoleFilterRequestData,
)
from family_tree_api_client.models.role_get_response import RoleGetResponse
from family_tree_api_client.models.role_sort_field import RoleSortField
from family_tree_api_client.models.role_update_date_request import (
    RoleUpdateDateRequest,
)
from family_tree_api_client.models.role_update_request import RoleUpdateRequest
from family_tree_api_client.models.role_update_response import RoleUpdateResponse
from family_tree_api_client.models.role_update_where_request import (
    RoleUpdateWhereRequest,
)
from family_tree_api_client.models.sort_order_field import SortOrderField
from family_tree_api_client.models.sort_request_params_role_sort_field import (
    SortRequestParamsRoleSortField,
)

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.infrastructure.services.unit_of_work.sqlalchemy_uow import SQLAlchemyUnitOfWork
from app.utils.error_codes import ERROR_MESSAGES, ErrorCode
from tests.e2e.auth_headers import admin_client as admin_client
from tests.e2e.auth_headers import member_client as member_client

# ============================================================
# CREATE ROLE
# ============================================================


@pytest.mark.asyncio
async def test_create_role_permission_denied(member_client: AuthenticatedClient):
    req = RoleCreateRequest(
        name="limited-role",
        permission_ids=[],
    )
    resp = await create_role(client=member_client, body=req)

    assert resp.status_code == 403

    body = json.loads(resp.content)
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_create_role_unauthenticated(client: Client):
    req = RoleCreateRequest(
        name="limited-role",
        permission_ids=[],
    )

    resp = await create_role(client=client, body=req)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_role_success(admin_client: AuthenticatedClient, uow):
    async with uow:
        perm_01 = await uow.permissions.create(permission=Permission(name="perm_01"))
        perm_02 = await uow.permissions.create(permission=Permission(name="perm_02"))
        await uow.commit()

    req = RoleCreateRequest(
        name="my-admin-role",
        permission_ids=[perm_01.safe_id, perm_02.safe_id],
    )

    resp = await create_role(client=admin_client, body=req)

    assert resp.status_code == 201

    assert isinstance(resp.parsed, RoleCreateResponse)
    role_data = resp.parsed

    assert role_data.id is not None
    assert role_data.name == req.name

    async with uow:
        find_role = await uow.roles.get_or_raise(role_id=role_data.id)

    assert find_role.id == role_data.id
    assert find_role.name == role_data.name
    assert find_role.permission_ids == [perm_01.safe_id, perm_02.safe_id]


@pytest.mark.asyncio
async def test_create_role_with_duplicate_name(
    admin_client: AuthenticatedClient,
    uow: SQLAlchemyUnitOfWork,
):
    perm_01 = await uow.permissions.create(permission=Permission(name="perm_01"))
    perm_02 = await uow.permissions.create(permission=Permission(name="perm_02"))

    role = Role(
        name="duplicate-role",
        permission_ids=[perm_01.safe_id, perm_02.safe_id],
    )
    await uow.roles.create(role=role)
    await uow.commit()

    payload = RoleCreateRequest(
        name=role.name,
        permission_ids=[],
    )

    response = await create_role(client=admin_client, body=payload)

    assert response.status_code == 409
    body = json.loads(response.content)
    assert body["error_code"] == 1501
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.ROLE_NAME_DUPLICATED]
    assert body["status"] == 409


# ============================================================
# GET ROLE
# ============================================================


@pytest.mark.asyncio
async def test_get_role_permission_denied(member_client: AuthenticatedClient):
    resp = await get_role(role_id=UUID(int=1), client=member_client)

    body = json.loads(resp.content)
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_get_role_unauthenticated(client: Client):
    resp = await get_role(role_id=UUID(int=1), client=client)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_role_success(
    admin_client: AuthenticatedClient, uow: SQLAlchemyUnitOfWork
):
    perm_01 = await uow.permissions.create(permission=Permission(name="perm_01"))
    perm_02 = await uow.permissions.create(permission=Permission(name="perm_02"))

    role_data = Role(
        name="duplicate-role",
        permission_ids=[perm_01.safe_id, perm_02.safe_id],
    )
    role = await uow.roles.create(role=role_data)
    await uow.commit()

    resp = await get_role(role_id=role.safe_id, client=admin_client)

    assert resp.status_code == 200

    assert isinstance(resp.parsed, RoleGetResponse)
    data = resp.parsed

    assert data.id == role.safe_id
    assert data.name == role.name
    assert data.id == role.id
    assert data.permission_ids == role.permission_ids


@pytest.mark.asyncio
async def test_get_role_with_invalid_id(admin_client: AuthenticatedClient):
    invalid_role_id = UUID(int=999999)

    resp = await get_role(role_id=invalid_role_id, client=admin_client)

    assert resp.status_code == 404

    body = json.loads(resp.content)
    assert body["error_code"] == 1500
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.ROLE_NOT_FOUND]


# ============================================================
# UPDATE ROLE
# ============================================================


@pytest.mark.asyncio
async def test_update_role_permission_denied(member_client: AuthenticatedClient):
    payload = RoleUpdateRequest(
        where=RoleUpdateWhereRequest(role_id=UUID(int=1)),
        data=RoleUpdateDateRequest(name="123", permission_ids=[]),
    )

    resp = await update_role(client=member_client, body=payload)

    assert resp.status_code == 403

    body = json.loads(resp.content)
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_update_role_unauthenticated(client: Client):
    payload = RoleUpdateRequest(
        where=RoleUpdateWhereRequest(role_id=UUID(int=1)),
        data=RoleUpdateDateRequest(name="123", permission_ids=[]),
    )

    resp = await update_role(client=client, body=payload)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_role_success(
    admin_client: AuthenticatedClient, uow: SQLAlchemyUnitOfWork
):
    perm1 = await uow.permissions.create(permission=Permission(name="perm1"))
    perm2 = await uow.permissions.create(permission=Permission(name="perm2"))
    perm3 = await uow.permissions.create(permission=Permission(name="perm3"))

    new_role = Role(name="newwww", permission_ids=[perm1.safe_id, perm2.safe_id])
    role = await uow.roles.create(role=new_role)
    await uow.commit()

    payload = RoleUpdateRequest(
        where=RoleUpdateWhereRequest(role_id=role.safe_id),
        data=RoleUpdateDateRequest(
            name="updated_name", permission_ids=[perm1.safe_id, perm3.safe_id]
        ),
    )

    resp = await update_role(client=admin_client, body=payload)

    assert resp.status_code == 200

    assert isinstance(resp.parsed, RoleUpdateResponse)

    async with uow:
        role = await uow.roles.get_or_raise(role_id=role.safe_id)

    assert role.name == payload.data.name
    assert role.permission_ids == payload.data.permission_ids
    assert role.id == payload.where.role_id


@pytest.mark.asyncio
async def test_update_role_with_invalid_id(admin_client: AuthenticatedClient):
    payload = RoleUpdateRequest(
        where=RoleUpdateWhereRequest(role_id=UUID(int=88888)),
        data=RoleUpdateDateRequest(name="new_role", permission_ids=[]),
    )

    resp = await update_role(client=admin_client, body=payload)

    assert resp.status_code == 404

    body = json.loads(resp.content)
    assert body["error_code"] == 1500
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.ROLE_NOT_FOUND]


@pytest.mark.asyncio
async def test_update_role_with_duplicate_name(
    admin_client: AuthenticatedClient,
    uow: SQLAlchemyUnitOfWork,
):
    new_role1 = Role(name="new_role1", permission_ids=[])
    role1 = await uow.roles.create(role=new_role1)

    new_role2 = Role(name="new_role2", permission_ids=[])
    role2 = await uow.roles.create(role=new_role2)

    await uow.commit()

    payload = RoleUpdateRequest(
        where=RoleUpdateWhereRequest(role_id=role2.safe_id),
        data=RoleUpdateDateRequest(name=role1.name, permission_ids=[]),
    )

    response = await update_role(client=admin_client, body=payload)

    assert response.status_code == 409
    body = json.loads(response.content)
    assert body["error_code"] == 1501
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.ROLE_NAME_DUPLICATED]
    assert body["status"] == 409


# ============================================================
# DELETE ROLE
# ============================================================


@pytest.mark.asyncio
async def test_delete_role_permission_denied(member_client: AuthenticatedClient):
    resp = await delete_role(role_id=UUID(int=1), client=member_client)

    body = json.loads(resp.content)
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_delete_role_unauthenticated(client: Client):
    resp = await delete_role(role_id=UUID(int=1), client=client)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_role_success(
    admin_client: AuthenticatedClient, uow: SQLAlchemyUnitOfWork
):
    perm1 = await uow.permissions.create(permission=Permission(name="perm1"))
    perm2 = await uow.permissions.create(permission=Permission(name="perm2"))

    new_role = Role(name="newwww", permission_ids=[perm1.safe_id, perm2.safe_id])
    role = await uow.roles.create(role=new_role)
    await uow.commit()

    resp = await delete_role(role_id=role.safe_id, client=admin_client)

    assert resp.status_code == 200

    assert isinstance(resp.parsed, ResultResponse)

    deleted_role_id = role.safe_id
    async with uow:
        deleted_role = await uow.roles.get(role_id=deleted_role_id)

    assert deleted_role is None


@pytest.mark.asyncio
async def test_delete_role_with_invalid_id(admin_client: AuthenticatedClient):
    invalid_role_id = UUID(int=999999)

    resp = await delete_role(role_id=invalid_role_id, client=admin_client)

    assert resp.status_code == 404

    body = json.loads(resp.content)
    assert body["error_code"] == 1500
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.ROLE_NOT_FOUND]


# ============================================================
# LIST ROLES
# ============================================================


@pytest.mark.asyncio
async def test_get_role_list_by_filter_permission_denied(
    member_client: AuthenticatedClient,
):
    req = FilterRoleRequest(
        filters=RoleFilterRequestData(),
        pagination=PaginationRequestParams(
            offset=0,
            page=1,
            page_size=30,
        ),
        sort=SortRequestParamsRoleSortField(
            sort_by=RoleSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    resp = await get_role_list_by_filter(client=member_client, body=req)

    body = json.loads(resp.content)
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_get_role_list_by_filter_unauthenticated(client: Client):
    req = FilterRoleRequest(
        filters=RoleFilterRequestData(),
        pagination=PaginationRequestParams(
            offset=0,
            page=1,
            page_size=30,
        ),
        sort=SortRequestParamsRoleSortField(
            sort_by=RoleSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    resp = await get_role_list_by_filter(client=client, body=req)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_role_list_by_filter_success(
    admin_client: AuthenticatedClient,
    uow: SQLAlchemyUnitOfWork,
):
    perm1 = await uow.permissions.create(permission=Permission(name="perm1"))
    perm2 = await uow.permissions.create(permission=Permission(name="perm2"))
    perm3 = await uow.permissions.create(permission=Permission(name="perm3"))
    perm4 = await uow.permissions.create(permission=Permission(name="perm4"))
    perm5 = await uow.permissions.create(permission=Permission(name="perm5"))
    perm6 = await uow.permissions.create(permission=Permission(name="perm6"))

    role1 = await uow.roles.create(
        role=Role(name="cus_role1", permission_ids=[perm1.safe_id, perm2.safe_id])
    )
    role2 = await uow.roles.create(
        role=Role(name="cus_role2", permission_ids=[perm1.safe_id, perm3.safe_id])
    )
    role3 = await uow.roles.create(
        role=Role(name="cus_role3", permission_ids=[perm1.safe_id, perm4.safe_id])
    )
    role4 = await uow.roles.create(
        role=Role(name="cus_role4", permission_ids=[perm1.safe_id, perm5.safe_id])
    )
    role5 = await uow.roles.create(
        role=Role(name="cus_role5", permission_ids=[perm1.safe_id, perm6.safe_id])
    )
    await uow.commit()

    req = FilterRoleRequest(
        filters=RoleFilterRequestData(
            name="cus_role",
            permission_id=perm1.safe_id,
        ),
        pagination=PaginationRequestParams(
            offset=1,
            page=2,
            page_size=2,
        ),
        sort=SortRequestParamsRoleSortField(
            sort_by=RoleSortField.ID,
            sort_order=SortOrderField.ASC,
        ),
    )

    resp = await get_role_list_by_filter(client=admin_client, body=req)

    assert resp.status_code == 200

    assert isinstance(resp.parsed, PaginatedResponseRoleModel)
    data = resp.parsed
    sorted_roles = sorted(
        [role1, role2, role3, role4, role5], key=lambda role: role.safe_id
    )
    start = req.pagination.offset + (req.pagination.page - 1) * req.pagination.page_size
    expected = sorted_roles[start : start + req.pagination.page_size]

    assert len(data.items) == 2
    assert data.items[0].id == expected[0].safe_id
    assert data.items[0].name == expected[0].name
    assert data.items[1].id == expected[1].safe_id
    assert data.items[1].name == expected[1].name
    assert sorted(data.items[0].permission_ids) == sorted(expected[0].permission_ids)
    assert sorted(data.items[1].permission_ids) == sorted(expected[1].permission_ids)
