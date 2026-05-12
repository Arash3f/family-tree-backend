import pytest
from pydantic import TypeAdapter

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.shared.dto.role_filter_dto import RoleSortField
from app.domain.shared.dto.sorter_dto import SortOrderField
from app.infrastructure.services.unit_of_work.sqlalchemy_uow import SQLAlchemyUnitOfWork
from app.presentation.rest.schemas.dto.common import (
    PaginatedResponse,
    PaginationRequestParams,
    ResultResponse,
    SortRequestParams,
)
from app.presentation.rest.schemas.dto.role_schema import (
    FilterRoleRequest,
    RoleCreateRequest,
    RoleCreateResponse,
    RoleFilterRequestData,
    RoleGetResponse,
    RoleModel,
    RoleUpdateRequest,
    RoleUpdateResponse,
    _RoleUpdateDateRequest,
    _RoleUpdateWhereRequest,
)
from app.utils.error_codes import ERROR_MESSAGES, ErrorCode
from tests.e2e.auth_headers import admin_headers as admin_headers
from tests.e2e.auth_headers import member_headers as member_headers

BASE_URL = "/roles"


# ============================================================
# CREATE ROLE
# ============================================================


@pytest.mark.asyncio
async def test_create_role_permission_denied(client, member_headers):  # noqa: F811
    req = RoleCreateRequest(
        name="limited-role",
        permission_ids=[],
    )
    resp = await client.post(
        f"{BASE_URL}/",
        json=req.model_dump(),
        headers=member_headers,
    )

    assert resp.status_code == 403

    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_create_role_unauthenticated(client):  # noqa: F811
    req = RoleCreateRequest(
        name="limited-role",
        permission_ids=[],
    )

    resp = await client.post(
        f"{BASE_URL}/",
        json=req.model_dump(),
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_role_success(client, admin_headers, uow):  # noqa: F811
    async with uow:
        perm_01 = await uow.permissions.create(permission=Permission(name="perm_01"))
        perm_02 = await uow.permissions.create(permission=Permission(name="perm_02"))
        await uow.commit()

    req = RoleCreateRequest(
        name="my-admin-role",
        permission_ids=[perm_01.safe_id, perm_02.safe_id],
    )

    resp = await client.post(
        f"{BASE_URL}/",
        json=req.model_dump(),
        headers=admin_headers,
    )

    assert resp.status_code == 201

    role_data = TypeAdapter(RoleCreateResponse).validate_python(resp.json())

    assert role_data.id > 0
    assert role_data.name == req.name

    async with uow:
        find_role = await uow.roles.get_or_raise(role_id=role_data.id)

    assert find_role.id == role_data.id
    assert find_role.name == role_data.name
    assert find_role.permission_ids == [perm_01.safe_id, perm_02.safe_id]


@pytest.mark.asyncio
async def test_create_role_with_duplicate_name(
    client,
    admin_headers,  # noqa: F811
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

    response = await client.post(
        f"{BASE_URL}/",
        json=payload.model_dump(),
        headers=admin_headers,
    )

    assert response.status_code == 409
    assert response.json()["error_code"] == 1501
    assert (
        response.json()["message"]
        == ERROR_MESSAGES["en"][ErrorCode.ROLE_NAME_DUPLICATED]
    )
    assert response.json()["status"] == 409


# ============================================================
# GET ROLE
# ============================================================


@pytest.mark.asyncio
async def test_get_role_permission_denied(client, member_headers):  # noqa: F811
    resp = await client.get(
        f"{BASE_URL}/1",
        headers=member_headers,
    )

    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_get_role_unauthenticated(client):  # noqa: F811
    resp = await client.get(f"{BASE_URL}/1")

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_role_success(client, admin_headers, uow: SQLAlchemyUnitOfWork):  # noqa: F811
    perm_01 = await uow.permissions.create(permission=Permission(name="perm_01"))
    perm_02 = await uow.permissions.create(permission=Permission(name="perm_02"))

    role_data = Role(
        name="duplicate-role",
        permission_ids=[perm_01.safe_id, perm_02.safe_id],
    )
    role = await uow.roles.create(role=role_data)
    await uow.commit()

    resp = await client.get(
        f"{BASE_URL}/{role.safe_id}",
        headers=admin_headers,
    )

    assert resp.status_code == 200

    data = TypeAdapter(RoleGetResponse).validate_python(resp.json())

    assert data.id == role.safe_id
    assert data.name == role.name
    assert data.id == role.id
    assert data.permission_ids == role.permission_ids


@pytest.mark.asyncio
async def test_get_role_with_invalid_id(client, admin_headers):  # noqa: F811
    invalid_role_id = 999999

    resp = await client.get(
        f"{BASE_URL}/{invalid_role_id}",
        headers=admin_headers,
    )

    assert resp.status_code == 404

    body = resp.json()
    assert body["error_code"] == 1500
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.ROLE_NOT_FOUND]


# ============================================================
# UPDATE ROLE
# ============================================================


@pytest.mark.asyncio
async def test_update_role_permission_denied(client, member_headers):  # noqa: F811
    payload = RoleUpdateRequest(
        where=_RoleUpdateWhereRequest(role_id=1),
        data=_RoleUpdateDateRequest(name="123", permission_ids=[]),
    )

    resp = await client.put(
        f"{BASE_URL}/",
        json=payload.model_dump(),
        headers=member_headers,
    )

    assert resp.status_code == 403

    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_update_role_unauthenticated(client):  # noqa: F811
    payload = RoleUpdateRequest(
        where=_RoleUpdateWhereRequest(role_id=1),
        data=_RoleUpdateDateRequest(name="123", permission_ids=[]),
    )

    resp = await client.put(
        f"{BASE_URL}/",
        json=payload.model_dump(),
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_role_success(client, admin_headers, uow: SQLAlchemyUnitOfWork):  # noqa: F811
    perm1 = await uow.permissions.create(permission=Permission(name="perm1"))
    perm2 = await uow.permissions.create(permission=Permission(name="perm2"))
    perm3 = await uow.permissions.create(permission=Permission(name="perm3"))

    new_role = Role(name="newwww", permission_ids=[perm1.safe_id, perm2.safe_id])
    role = await uow.roles.create(role=new_role)
    await uow.commit()

    payload = RoleUpdateRequest(
        where=_RoleUpdateWhereRequest(role_id=role.safe_id),
        data=_RoleUpdateDateRequest(
            name="updated_name", permission_ids=[perm1.safe_id, perm3.safe_id]
        ),
    )

    resp = await client.put(
        f"{BASE_URL}/",
        json=payload.model_dump(),
        headers=admin_headers,
    )

    assert resp.status_code == 200

    TypeAdapter(RoleUpdateResponse).validate_python(resp.json())

    async with uow:
        role = await uow.roles.get_or_raise(role_id=role.safe_id)

    assert role.name == payload.data.name
    assert role.permission_ids == payload.data.permission_ids
    assert role.id == payload.where.role_id


@pytest.mark.asyncio
async def test_update_role_with_invalid_id(client, admin_headers):  # noqa: F811
    payload = RoleUpdateRequest(
        where=_RoleUpdateWhereRequest(role_id=88888),
        data=_RoleUpdateDateRequest(name="new_role", permission_ids=[]),
    )

    resp = await client.put(
        f"{BASE_URL}/",
        json=payload.model_dump(),
        headers=admin_headers,
    )

    assert resp.status_code == 404

    body = resp.json()
    assert body["error_code"] == 1500
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.ROLE_NOT_FOUND]


@pytest.mark.asyncio
async def test_update_role_with_duplicate_name(
    client,
    admin_headers,  # noqa: F811
    uow: SQLAlchemyUnitOfWork,
):
    new_role1 = Role(name="new_role1", permission_ids=[])
    role1 = await uow.roles.create(role=new_role1)

    new_role2 = Role(name="new_role2", permission_ids=[])
    role2 = await uow.roles.create(role=new_role2)

    await uow.commit()

    payload = RoleUpdateRequest(
        where=_RoleUpdateWhereRequest(role_id=role2.safe_id),
        data=_RoleUpdateDateRequest(name=role1.name, permission_ids=[]),
    )

    response = await client.put(
        f"{BASE_URL}/",
        json=payload.model_dump(),
        headers=admin_headers,
    )

    assert response.status_code == 409
    assert response.json()["error_code"] == 1501
    assert (
        response.json()["message"]
        == ERROR_MESSAGES["en"][ErrorCode.ROLE_NAME_DUPLICATED]
    )
    assert response.json()["status"] == 409


# ============================================================
# DELETE ROLE
# ============================================================


@pytest.mark.asyncio
async def test_delete_role_permission_denied(client, member_headers):  # noqa: F811
    resp = await client.delete(
        f"{BASE_URL}/1",
        headers=member_headers,
    )

    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_delete_role_unauthenticated(client):  # noqa: F811
    resp = await client.delete(f"{BASE_URL}/1")

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_role_success(client, admin_headers, uow: SQLAlchemyUnitOfWork):  # noqa: F811
    perm1 = await uow.permissions.create(permission=Permission(name="perm1"))
    perm2 = await uow.permissions.create(permission=Permission(name="perm2"))

    new_role = Role(name="newwww", permission_ids=[perm1.safe_id, perm2.safe_id])
    role = await uow.roles.create(role=new_role)
    await uow.commit()

    resp = await client.delete(
        f"{BASE_URL}/{role.safe_id}",
        headers=admin_headers,
    )

    assert resp.status_code == 200

    TypeAdapter(ResultResponse).validate_python(resp.json())

    async with uow:
        role = await uow.roles.get(role_id=role.safe_id)

    assert role is None


@pytest.mark.asyncio
async def test_delete_role_with_invalid_id(client, admin_headers):  # noqa: F811
    invalid_role_id = 999999

    resp = await client.delete(
        f"{BASE_URL}/{invalid_role_id}",
        headers=admin_headers,
    )

    assert resp.status_code == 404

    body = resp.json()
    assert body["error_code"] == 1500
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.ROLE_NOT_FOUND]


# ============================================================
# LIST ROLES
# ============================================================


@pytest.mark.asyncio
async def test_get_role_list_by_filter_permission_denied(client, member_headers):  # noqa: F811
    req = FilterRoleRequest(
        filters=RoleFilterRequestData(),
        pagination=PaginationRequestParams(
            offset=0,
            page=1,
            page_size=30,
        ),
        sort=SortRequestParams(
            sort_by=RoleSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    resp = await client.post(
        f"{BASE_URL}/list",
        json=req.model_dump(),
        headers=member_headers,
    )

    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_get_role_list_by_filter_unauthenticated(client):  # noqa: F811
    req = FilterRoleRequest(
        filters=RoleFilterRequestData(),
        pagination=PaginationRequestParams(
            offset=0,
            page=1,
            page_size=30,
        ),
        sort=SortRequestParams(
            sort_by=RoleSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    resp = await client.post(
        f"{BASE_URL}/list",
        json=req.model_dump(),
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_role_list_by_filter_success(
    client,
    admin_headers,  # noqa: F811
    uow: SQLAlchemyUnitOfWork,
):
    perm1 = await uow.permissions.create(permission=Permission(name="perm1"))
    perm2 = await uow.permissions.create(permission=Permission(name="perm2"))
    perm3 = await uow.permissions.create(permission=Permission(name="perm3"))
    perm4 = await uow.permissions.create(permission=Permission(name="perm4"))
    perm5 = await uow.permissions.create(permission=Permission(name="perm5"))
    perm6 = await uow.permissions.create(permission=Permission(name="perm6"))

    await uow.roles.create(
        role=Role(name="cus_role1", permission_ids=[perm1.safe_id, perm2.safe_id])
    )
    await uow.roles.create(
        role=Role(name="cus_role2", permission_ids=[perm1.safe_id, perm3.safe_id])
    )
    await uow.roles.create(
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
        sort=SortRequestParams(
            sort_by=RoleSortField.ID,
            sort_order=SortOrderField.ASC,
        ),
    )

    resp = await client.post(
        f"{BASE_URL}/list",
        json=req.model_dump(),
        headers=admin_headers,
    )

    assert resp.status_code == 200

    data = TypeAdapter(PaginatedResponse[RoleModel]).validate_python(resp.json())
    assert len(data.items) == 2
    assert data.items[0].id == role4.safe_id
    assert data.items[0].name == role4.name
    assert data.items[1].id == role5.safe_id
    assert data.items[1].name == role5.name
    assert sorted(data.items[0].permission_ids) == sorted(role4.permission_ids)
    assert sorted(data.items[1].permission_ids) == sorted(role5.permission_ids)
