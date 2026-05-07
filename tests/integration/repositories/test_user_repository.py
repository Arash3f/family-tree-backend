import pytest

from app.application.services.unit_of_work import UnitOfWork
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.domain.exceptions.user_exceptions import UserNotFoundException
from app.domain.shared.dto.pagination_dto import PaginatedResult, PaginationParams
from app.domain.shared.dto.sorter_dto import SortOrderField, SortParams
from app.domain.shared.dto.user_filter_dto import (
    FilterUserQuery,
    UserFilterDTO,
    UserSortField,
)


@pytest.mark.asyncio
async def test_create_and_get_user(uow: UnitOfWork):
    async with uow:
        new_role_data = Role(id=None, name="new_role", permission_ids=[])
        new_role = await uow.roles.create(role=new_role_data)

        new_user = User(
            id=None,
            username="test_user",
            password_hash="hashed_password",
            role_id=new_role.safe_id,
        )

        created = await uow.users.create(new_user)
        fetched = await uow.users.get(user_id=created.safe_id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.username == new_user.username
        assert fetched.password_hash == new_user.password_hash
        assert fetched.role_id == new_role.safe_id


@pytest.mark.asyncio
async def test_get_returns_none_when_not_found(uow: UnitOfWork):
    async with uow:
        result = await uow.users.get(user_id=999_999)
        assert result is None


@pytest.mark.asyncio
async def test_get_or_raise_success(uow: UnitOfWork):
    async with uow:
        new_role_data = Role(id=None, name="new_role", permission_ids=[])
        new_role = await uow.roles.create(role=new_role_data)
        user = User(
            id=None,
            username="get_or_raise_user",
            password_hash="hashed_password",
            role_id=new_role.safe_id,
        )

        created = await uow.users.create(user)

        fetched = await uow.users.get_or_raise(user_id=created.safe_id)

        assert fetched.id == created.id
        assert fetched.username == user.username


@pytest.mark.asyncio
async def test_get_or_raise_not_found(uow: UnitOfWork):
    async with uow:
        with pytest.raises(UserNotFoundException):
            await uow.users.get_or_raise(user_id=123456)


@pytest.mark.asyncio
async def test_get_by_username_found(uow: UnitOfWork):
    async with uow:
        new_role_data = Role(id=None, name="new_role", permission_ids=[])
        new_role = await uow.roles.create(role=new_role_data)
        user = User(
            id=None,
            username="unique_username",
            password_hash="hashed_password",
            role_id=new_role.safe_id,
        )

        created = await uow.users.create(user)

        fetched = await uow.users.get_by_username(username="unique_username")

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.username == "unique_username"


@pytest.mark.asyncio
async def test_get_by_username_not_found(uow: UnitOfWork):
    async with uow:
        result = await uow.users.get_by_username(username="unknown_username")
        assert result is None


@pytest.mark.asyncio
async def test_get_list_by_filter_with_username_partial_match(uow: UnitOfWork):
    async with uow:
        created_users = []

        for i in range(3):
            role_data = Role(id=None, name=f"new_role_{i}", permission_ids=[])
            role = await uow.roles.create(role=role_data)
            user = await uow.users.create(
                User(
                    id=None,
                    username=f"user_{i}",
                    password_hash=f"p_{i}",
                    role_id=role.safe_id,
                )
            )
            created_users.append(user)

        query = FilterUserQuery(
            filters=UserFilterDTO(
                username="er_1",
            ),
            pagination=PaginationParams(
                page=1,
                page_size=10,
                offset=0,
            ),
            sort=SortParams(
                sort_by=UserSortField.USERNAME,
                sort_order=SortOrderField.ASC,
            ),
        )

        result: PaginatedResult[User] = await uow.users.get_list_by_filter(query)

        usernames = [u.username for u in result.items]

        assert "user_1" in usernames
        assert "user_0" not in usernames
        assert "user_2" not in usernames
        assert result.total >= 1
        assert len(result.items) >= 1


@pytest.mark.asyncio
async def test_get_list_by_filter_with_pagination(uow: UnitOfWork):
    async with uow:
        created_users = []

        for i in range(10):
            role_data = Role(id=None, name=f"new_role_{i}", permission_ids=[])
            role = await uow.roles.create(role=role_data)
            user = await uow.users.create(
                User(
                    id=None,
                    username=f"user_{i}",
                    password_hash=f"p_{i}",
                    role_id=role.safe_id,
                )
            )
            created_users.append(user)

        query = FilterUserQuery(
            filters=None,
            pagination=PaginationParams(
                page=2,
                page_size=2,
                offset=5,
            ),
            sort=SortParams(
                sort_by=UserSortField.ID,
                sort_order=SortOrderField.ASC,
            ),
        )

        result: PaginatedResult[User] = await uow.users.get_list_by_filter(query)

        assert result.page == query.pagination.page
        assert result.page_size == query.pagination.page_size
        assert len(result.items) == query.pagination.page_size
        assert result.total >= 10

        returned_usernames = [u.username for u in result.items]

        assert "user_7" in returned_usernames
        assert "user_8" in returned_usernames


@pytest.mark.asyncio
async def test_update_user(uow: UnitOfWork):
    async with uow:
        new_role_data = Role(id=None, name="new_role", permission_ids=[])
        new_role = await uow.roles.create(role=new_role_data)
        user = User(
            id=None,
            username="old_username",
            password_hash="old_hash",
            role_id=new_role.safe_id,
        )
        created = await uow.users.create(user)

        new_role_data_2 = Role(id=None, name="new_role_2", permission_ids=[])
        new_role_2 = await uow.roles.create(role=new_role_data_2)
        created.username = "new_username"
        created.password_hash = "new_hash"
        created.role_id = new_role_2.safe_id

        updated = await uow.users.update(created)

        assert updated.id == created.id
        assert updated.username == "new_username"
        assert updated.password_hash == "new_hash"
        assert updated.role_id == new_role_2.safe_id

        fetched = await uow.users.get_or_raise(user_id=created.safe_id)
        assert fetched.username == "new_username"
        assert fetched.password_hash == "new_hash"
        assert fetched.role_id == new_role_2.safe_id


@pytest.mark.asyncio
async def test_update_user_not_found_raises_domain_exception(uow: UnitOfWork):
    async with uow:
        fake_user = User(
            id=999999,
            username="non_existing",
            password_hash="x",
            role_id=1,
        )

        with pytest.raises(UserNotFoundException):
            await uow.users.update(fake_user)


@pytest.mark.asyncio
async def test_delete_user(uow: UnitOfWork):
    async with uow:
        new_role_data = Role(id=None, name="new_role", permission_ids=[])
        new_role = await uow.roles.create(role=new_role_data)
        user = User(
            id=None,
            username="to_be_deleted",
            password_hash="hash",
            role_id=new_role.safe_id,
        )
        created = await uow.users.create(user)

        await uow.users.delete(user_id=created.safe_id)

        fetched = await uow.users.get(user_id=created.safe_id)
        assert fetched is None
