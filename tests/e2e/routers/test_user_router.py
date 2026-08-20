import json
from uuid import UUID

import pytest
from family_tree_api_client import AuthenticatedClient, Client
from family_tree_api_client.api.users.create_user_users_post import (
    asyncio_detailed as create_user,
)
from family_tree_api_client.api.users.delete_user_users_user_id_delete import (
    asyncio_detailed as delete_user,
)
from family_tree_api_client.api.users.get_user_list_by_filter_users_list_post import (
    asyncio_detailed as get_user_list_by_filter,
)
from family_tree_api_client.api.users.get_user_users_user_id_get import (
    asyncio_detailed as get_user,
)
from family_tree_api_client.api.users.update_user_users_put import (
    asyncio_detailed as update_user,
)
from family_tree_api_client.models.filter_user_request import FilterUserRequest
from family_tree_api_client.models.paginated_response_user_model import (
    PaginatedResponseUserModel,
)
from family_tree_api_client.models.pagination_request_params import (
    PaginationRequestParams,
)
from family_tree_api_client.models.result_response import ResultResponse
from family_tree_api_client.models.sort_order_field import SortOrderField
from family_tree_api_client.models.sort_request_params_user_sort_field import (
    SortRequestParamsUserSortField,
)
from family_tree_api_client.models.user_create_request import UserCreateRequest
from family_tree_api_client.models.user_create_response import UserCreateResponse
from family_tree_api_client.models.user_filter_request_data import (
    UserFilterRequestData,
)
from family_tree_api_client.models.user_get_response import UserGetResponse
from family_tree_api_client.models.user_sort_field import UserSortField
from family_tree_api_client.models.user_update_date_request import (
    UserUpdateDateRequest,
)
from family_tree_api_client.models.user_update_request import UserUpdateRequest
from family_tree_api_client.models.user_update_response import UserUpdateResponse
from family_tree_api_client.models.user_update_where_request import (
    UserUpdateWhereRequest,
)

from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.infrastructure.services.security.password_hasher_impl import (
    Argon2PasswordHasher,
)
from app.infrastructure.services.unit_of_work.sqlalchemy_uow import SQLAlchemyUnitOfWork
from app.utils.error_codes import ERROR_MESSAGES, ErrorCode
from tests.e2e.auth_headers import admin_client as admin_client
from tests.e2e.auth_headers import member_client as member_client

# ============================================================
# CREATE USER
# ============================================================


@pytest.mark.asyncio
async def test_create_user_permission_denied(member_client: AuthenticatedClient):
    req = UserCreateRequest(
        username="limited-user",
        fullname="limited-user",
        password="secret",
        re_password="secret",
    )
    resp = await create_user(client=member_client, body=req)

    assert resp.status_code == 403
    body = json.loads(resp.content)
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_create_user_unauthenticated(client: Client):
    req = UserCreateRequest(
        username="limited-user",
        fullname="limited-user",
        password="secret",
        re_password="secret",
    )
    resp = await create_user(client=client, body=req)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_user_success(admin_client: AuthenticatedClient, uow):
    role = await uow.roles.create(Role(name="custom-role", permission_ids=[]))
    await uow.commit()

    req = UserCreateRequest(
        username="new-user",
        fullname="New User",
        password="secret123",
        re_password="secret123",
        role_id=role.safe_id,
    )

    resp = await create_user(client=admin_client, body=req)

    assert resp.status_code == 200

    assert isinstance(resp.parsed, UserCreateResponse)
    user_data = resp.parsed
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
async def test_get_user_permission_denied(member_client: AuthenticatedClient):
    resp = await get_user(user_id=UUID(int=1), client=member_client)

    body = json.loads(resp.content)
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_get_user_unauthenticated(client: Client):
    resp = await get_user(user_id=UUID(int=1), client=client)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_user_success(
    admin_client: AuthenticatedClient, uow: SQLAlchemyUnitOfWork
):
    hasher = Argon2PasswordHasher()
    user = await uow.users.create(
        User(
            username="get-user",
            password_hash=hasher.hash("secret"),
        )
    )
    await uow.commit()

    resp = await get_user(user_id=user.safe_id, client=admin_client)

    assert resp.status_code == 200

    assert isinstance(resp.parsed, UserGetResponse)
    data = resp.parsed
    assert data.id == user.safe_id
    assert data.username == user.username


@pytest.mark.asyncio
async def test_get_user_with_invalid_id(admin_client: AuthenticatedClient):
    resp = await get_user(user_id=UUID(int=999999), client=admin_client)

    assert resp.status_code == 404
    body = json.loads(resp.content)
    assert body["error_code"] == 1400
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.USER_NOT_FOUND]


# ============================================================
# UPDATE USER
# ============================================================


@pytest.mark.asyncio
async def test_update_user_permission_denied(member_client: AuthenticatedClient):
    payload = UserUpdateRequest(
        where=UserUpdateWhereRequest(user_id=UUID(int=1)),
        data=UserUpdateDateRequest(username="updated"),
    )

    resp = await update_user(client=member_client, body=payload)

    assert resp.status_code == 403
    body = json.loads(resp.content)
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_update_user_unauthenticated(client: Client):
    payload = UserUpdateRequest(
        where=UserUpdateWhereRequest(user_id=UUID(int=1)),
        data=UserUpdateDateRequest(username="updated"),
    )

    resp = await update_user(client=client, body=payload)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_user_success(
    admin_client: AuthenticatedClient, uow: SQLAlchemyUnitOfWork
):
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
        where=UserUpdateWhereRequest(user_id=user.safe_id),
        data=UserUpdateDateRequest(
            username="new-username",
            role_id=role.safe_id,
        ),
    )

    resp = await update_user(client=admin_client, body=payload)

    assert resp.status_code == 200
    assert isinstance(resp.parsed, UserUpdateResponse)

    async with uow:
        updated = await uow.users.get_or_raise(user_id=user.safe_id)

    assert updated.username == payload.data.username
    assert updated.role_id == role.safe_id


@pytest.mark.asyncio
async def test_update_user_with_invalid_id(admin_client: AuthenticatedClient):
    payload = UserUpdateRequest(
        where=UserUpdateWhereRequest(user_id=UUID(int=88888)),
        data=UserUpdateDateRequest(username="new-username"),
    )

    resp = await update_user(client=admin_client, body=payload)

    assert resp.status_code == 404
    body = json.loads(resp.content)
    assert body["error_code"] == 1400
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.USER_NOT_FOUND]


# ============================================================
# DELETE USER
# ============================================================


@pytest.mark.asyncio
async def test_delete_user_permission_denied(member_client: AuthenticatedClient):
    resp = await delete_user(user_id=UUID(int=1), client=member_client)

    body = json.loads(resp.content)
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_delete_user_unauthenticated(client: Client):
    resp = await delete_user(user_id=UUID(int=1), client=client)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_user_success(
    admin_client: AuthenticatedClient, uow: SQLAlchemyUnitOfWork
):
    hasher = Argon2PasswordHasher()
    user = await uow.users.create(
        User(
            username="to-delete",
            password_hash=hasher.hash("secret"),
        )
    )
    await uow.commit()

    resp = await delete_user(user_id=user.safe_id, client=admin_client)

    assert resp.status_code == 200
    assert isinstance(resp.parsed, ResultResponse)

    deleted_user_id = user.safe_id
    async with uow:
        deleted = await uow.users.get(user_id=deleted_user_id)

    assert deleted is None


@pytest.mark.asyncio
async def test_delete_user_with_invalid_id(admin_client: AuthenticatedClient):
    resp = await delete_user(user_id=UUID(int=999999), client=admin_client)

    assert resp.status_code == 404
    body = json.loads(resp.content)
    assert body["error_code"] == 1400
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.USER_NOT_FOUND]


# ============================================================
# LIST USERS
# ============================================================


@pytest.mark.asyncio
async def test_get_user_list_by_filter_permission_denied(
    member_client: AuthenticatedClient,
):
    req = FilterUserRequest(
        filters=UserFilterRequestData(),
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParamsUserSortField(
            sort_by=UserSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    resp = await get_user_list_by_filter(client=member_client, body=req)

    body = json.loads(resp.content)
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_get_user_list_by_filter_unauthenticated(client: Client):
    req = FilterUserRequest(
        filters=UserFilterRequestData(),
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParamsUserSortField(
            sort_by=UserSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    resp = await get_user_list_by_filter(client=client, body=req)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_user_list_by_filter_success(
    admin_client: AuthenticatedClient,
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
        sort=SortRequestParamsUserSortField(
            sort_by=UserSortField.ID,
            sort_order=SortOrderField.ASC,
        ),
    )

    resp = await get_user_list_by_filter(client=admin_client, body=req)

    assert resp.status_code == 200

    assert isinstance(resp.parsed, PaginatedResponseUserModel)
    data = resp.parsed
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
