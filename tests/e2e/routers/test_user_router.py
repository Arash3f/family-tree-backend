from uuid import UUID

import pytest
from pydantic import TypeAdapter

from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.domain.shared.dto.sorter_dto import SortOrderField
from app.domain.shared.dto.user_filter_dto import UserSortField
from app.infrastructure.services.security.password_hasher_impl import (
    Argon2PasswordHasher,
)
from app.infrastructure.services.unit_of_work.sqlalchemy_uow import SQLAlchemyUnitOfWork
from app.presentation.rest.schemas.dto.common import (
    PaginatedResponse,
    PaginationRequestParams,
    ResultResponse,
    SortRequestParams,
)
from app.presentation.rest.schemas.dto.user_schema import (
    FilterUserRequest,
    UserCreateRequest,
    UserCreateResponse,
    UserFilterRequestData,
    UserGetResponse,
    UserModel,
    UserUpdateRequest,
    UserUpdateResponse,
    _UserUpdateDateRequest,
    _UserUpdateWhereRequest,
)
from app.utils.error_codes import ERROR_MESSAGES, ErrorCode
from tests.e2e.auth_headers import admin_headers as admin_headers
from tests.e2e.auth_headers import member_headers as member_headers

BASE_URL = "/users"


# ============================================================
# CREATE USER
# ============================================================


@pytest.mark.asyncio
async def test_create_user_permission_denied(client, member_headers):  # noqa: F811
    req = UserCreateRequest(
        username="limited-user",
        fullname="limited-user",
        password="secret",
        re_password="secret",
    )
    resp = await client.post(
        BASE_URL,
        json=req.model_dump(mode="json"),
        headers=member_headers,
    )

    assert resp.status_code == 403
    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_create_user_unauthenticated(client):
    req = UserCreateRequest(
        username="limited-user",
        fullname="limited-user",
        password="secret",
        re_password="secret",
    )
    resp = await client.post(
        BASE_URL,
        json=req.model_dump(mode="json"),
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_user_success(client, admin_headers, uow):  # noqa: F811
    role = await uow.roles.create(Role(name="custom-role", permission_ids=[]))
    await uow.commit()

    req = UserCreateRequest(
        username="new-user",
        fullname="New User",
        password="secret",
        re_password="secret",
        role_id=role.safe_id,
    )

    resp = await client.post(
        BASE_URL,
        json=req.model_dump(mode="json"),
        headers=admin_headers,
    )

    assert resp.status_code == 200

    user_data = TypeAdapter(UserCreateResponse).validate_python(resp.json())
    assert user_data.id is not None
    assert user_data.username == req.username
    assert user_data.fullname == req.fullname
    assert user_data.role_id == role.safe_id

    async with uow:
        find_user = await uow.users.get_or_raise(user_id=user_data.id)

    assert find_user.id == user_data.id
    assert find_user.username == user_data.username
    assert find_user.fullname == user_data.fullname
    assert find_user.role_id == role.safe_id


# ============================================================
# GET USER
# ============================================================


@pytest.mark.asyncio
async def test_get_user_permission_denied(client, member_headers):  # noqa: F811
    resp = await client.get(
        f"{BASE_URL}/{UUID(int=1)}",
        headers=member_headers,
    )

    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_get_user_unauthenticated(client):
    resp = await client.get(f"{BASE_URL}/{UUID(int=1)}")

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_user_success(client, admin_headers, uow: SQLAlchemyUnitOfWork):  # noqa: F811
    hasher = Argon2PasswordHasher()
    user = await uow.users.create(
        User(
            username="get-user",
            password_hash=hasher.hash("secret"),
        )
    )
    await uow.commit()

    resp = await client.get(
        f"{BASE_URL}/{user.safe_id}",
        headers=admin_headers,
    )

    assert resp.status_code == 200

    data = TypeAdapter(UserGetResponse).validate_python(resp.json())
    assert data.id == user.safe_id
    assert data.username == user.username


@pytest.mark.asyncio
async def test_get_user_with_invalid_id(client, admin_headers):  # noqa: F811
    resp = await client.get(
        f"{BASE_URL}/{UUID(int=999999)}",
        headers=admin_headers,
    )

    assert resp.status_code == 404
    body = resp.json()
    assert body["error_code"] == 1400
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.USER_NOT_FOUND]


# ============================================================
# UPDATE USER
# ============================================================


@pytest.mark.asyncio
async def test_update_user_permission_denied(client, member_headers):  # noqa: F811
    payload = UserUpdateRequest(
        where=_UserUpdateWhereRequest(user_id=UUID(int=1)),
        data=_UserUpdateDateRequest(username="updated"),
    )

    resp = await client.put(
        BASE_URL,
        json=payload.model_dump(mode="json"),
        headers=member_headers,
    )

    assert resp.status_code == 403
    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_update_user_unauthenticated(client):
    payload = UserUpdateRequest(
        where=_UserUpdateWhereRequest(user_id=UUID(int=1)),
        data=_UserUpdateDateRequest(username="updated"),
    )

    resp = await client.put(
        BASE_URL,
        json=payload.model_dump(mode="json"),
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_user_success(client, admin_headers, uow: SQLAlchemyUnitOfWork):  # noqa: F811
    hasher = Argon2PasswordHasher()
    role = await uow.roles.create(Role(name="update-role", permission_ids=[]))
    user = await uow.users.create(
        User(
            username="old-username",
            password_hash=hasher.hash("secret"),
        )
    )
    await uow.commit()

    payload = UserUpdateRequest(
        where=_UserUpdateWhereRequest(user_id=user.safe_id),
        data=_UserUpdateDateRequest(
            username="new-username",
            role_id=role.safe_id,
        ),
    )

    resp = await client.put(
        BASE_URL,
        json=payload.model_dump(mode="json"),
        headers=admin_headers,
    )

    assert resp.status_code == 200
    TypeAdapter(UserUpdateResponse).validate_python(resp.json())

    async with uow:
        updated = await uow.users.get_or_raise(user_id=user.safe_id)

    assert updated.username == payload.data.username
    assert updated.role_id == role.safe_id


@pytest.mark.asyncio
async def test_update_user_with_invalid_id(client, admin_headers):  # noqa: F811
    payload = UserUpdateRequest(
        where=_UserUpdateWhereRequest(user_id=UUID(int=88888)),
        data=_UserUpdateDateRequest(username="new-username"),
    )

    resp = await client.put(
        BASE_URL,
        json=payload.model_dump(mode="json"),
        headers=admin_headers,
    )

    assert resp.status_code == 404
    body = resp.json()
    assert body["error_code"] == 1400
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.USER_NOT_FOUND]


# ============================================================
# DELETE USER
# ============================================================


@pytest.mark.asyncio
async def test_delete_user_permission_denied(client, member_headers):  # noqa: F811
    resp = await client.delete(
        f"{BASE_URL}/{UUID(int=1)}",
        headers=member_headers,
    )

    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_delete_user_unauthenticated(client):
    resp = await client.delete(f"{BASE_URL}/{UUID(int=1)}")

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_user_success(client, admin_headers, uow: SQLAlchemyUnitOfWork):  # noqa: F811
    hasher = Argon2PasswordHasher()
    user = await uow.users.create(
        User(
            username="to-delete",
            password_hash=hasher.hash("secret"),
        )
    )
    await uow.commit()

    resp = await client.delete(
        f"{BASE_URL}/{user.safe_id}",
        headers=admin_headers,
    )

    assert resp.status_code == 200
    TypeAdapter(ResultResponse).validate_python(resp.json())

    deleted_user_id = user.safe_id
    async with uow:
        deleted = await uow.users.get(user_id=deleted_user_id)

    assert deleted is None


@pytest.mark.asyncio
async def test_delete_user_with_invalid_id(client, admin_headers):  # noqa: F811
    resp = await client.delete(
        f"{BASE_URL}/{UUID(int=999999)}",
        headers=admin_headers,
    )

    assert resp.status_code == 404
    body = resp.json()
    assert body["error_code"] == 1400
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.USER_NOT_FOUND]


# ============================================================
# LIST USERS
# ============================================================


@pytest.mark.asyncio
async def test_get_user_list_by_filter_permission_denied(client, member_headers):  # noqa: F811
    req = FilterUserRequest(
        filters=UserFilterRequestData(),
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParams(
            sort_by=UserSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    resp = await client.post(
        f"{BASE_URL}/list",
        json=req.model_dump(mode="json"),
        headers=member_headers,
    )

    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_get_user_list_by_filter_unauthenticated(client):
    req = FilterUserRequest(
        filters=UserFilterRequestData(),
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParams(
            sort_by=UserSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    resp = await client.post(
        f"{BASE_URL}/list",
        json=req.model_dump(mode="json"),
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_user_list_by_filter_success(
    client,
    admin_headers,  # noqa: F811
    uow: SQLAlchemyUnitOfWork,
):
    hasher = Argon2PasswordHasher()
    user1 = await uow.users.create(
        User(username="cus_user1", password_hash=hasher.hash("secret"))
    )
    user2 = await uow.users.create(
        User(username="cus_user2", password_hash=hasher.hash("secret"))
    )
    user3 = await uow.users.create(
        User(username="cus_user3", password_hash=hasher.hash("secret"))
    )
    user4 = await uow.users.create(
        User(username="cus_user4", password_hash=hasher.hash("secret"))
    )
    user5 = await uow.users.create(
        User(username="cus_user5", password_hash=hasher.hash("secret"))
    )
    await uow.commit()

    req = FilterUserRequest(
        filters=UserFilterRequestData(username="cus_user"),
        pagination=PaginationRequestParams(offset=1, page=2, page_size=2),
        sort=SortRequestParams(
            sort_by=UserSortField.ID,
            sort_order=SortOrderField.ASC,
        ),
    )

    resp = await client.post(
        f"{BASE_URL}/list",
        json=req.model_dump(mode="json"),
        headers=admin_headers,
    )

    assert resp.status_code == 200

    data = TypeAdapter(PaginatedResponse[UserModel]).validate_python(resp.json())
    sorted_users = sorted(
        [user1, user2, user3, user4, user5],
        key=lambda user: user.safe_id,
    )
    start = req.pagination.offset + (req.pagination.page - 1) * req.pagination.page_size
    expected = sorted_users[start : start + req.pagination.page_size]

    assert len(data.items) == 2
    assert data.items[0].id == expected[0].safe_id
    assert data.items[0].username == expected[0].username
    assert data.items[1].id == expected[1].safe_id
    assert data.items[1].username == expected[1].username
