import pytest

from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.permission import Permission
from app.domain.exceptions.permission_exceptions import PermissionNotFoundException
from app.domain.shared.dto.pagination_dto import PaginatedResult, PaginationParams
from app.domain.shared.dto.permission_filter_dto import (
    FilterPermissionQuery,
    PermissionFilterDTO,
    PermissionSortField,
)
from app.domain.shared.dto.sorter_dto import SortOrderField, SortParams


@pytest.mark.asyncio
async def test_create_and_get_permission(uow: UnitOfWork):
    async with uow:
        new_permission = Permission(
            id=None,
            name="can_view_users",
        )

        created = await uow.permissions.create(new_permission)
        fetched = await uow.permissions.get(permission_id=created.safe_id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == new_permission.name


@pytest.mark.asyncio
async def test_get_returns_none_when_not_found(uow: UnitOfWork):
    async with uow:
        result = await uow.permissions.get(permission_id=999_999)
        assert result is None


@pytest.mark.asyncio
async def test_get_or_raise_success(uow: UnitOfWork):
    async with uow:
        perm = Permission(id=None, name="can_edit_user")
        created = await uow.permissions.create(perm)

        fetched = await uow.permissions.get_or_raise(permission_id=created.safe_id)

        assert fetched.id == created.id
        assert fetched.name == "can_edit_user"


@pytest.mark.asyncio
async def test_get_or_raise_not_found(uow: UnitOfWork):
    async with uow:
        with pytest.raises(PermissionNotFoundException):
            await uow.permissions.get_or_raise(permission_id=123456)


@pytest.mark.asyncio
async def test_get_by_name_found(uow: UnitOfWork):
    async with uow:
        perm = Permission(id=None, name="can_delete_user")
        created = await uow.permissions.create(perm)

        fetched = await uow.permissions.get_by_name(name="can_delete_user")

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "can_delete_user"


@pytest.mark.asyncio
async def test_get_by_name_not_found(uow: UnitOfWork):
    async with uow:
        result = await uow.permissions.get_by_name(name="non_existing_permission_name")
        assert result is None


@pytest.mark.asyncio
async def test_get_list_returns_all_permissions(uow: UnitOfWork):
    async with uow:
        # create some permissions
        p1 = await uow.permissions.create(Permission(id=None, name="perm_a"))
        p2 = await uow.permissions.create(Permission(id=None, name="perm_b"))

        permissions = await uow.permissions.get_list()

        ids = {p.id for p in permissions}
        assert p1.id in ids
        assert p2.id in ids


@pytest.mark.asyncio
async def test_get_list_by_filter_with_name_partial_match(uow: UnitOfWork):
    async with uow:
        # seed some permissions
        await uow.permissions.create(Permission(id=None, name="user.read"))
        await uow.permissions.create(Permission(id=None, name="user.write"))
        await uow.permissions.create(Permission(id=None, name="admin.read"))

        query = FilterPermissionQuery(
            filters=PermissionFilterDTO(
                name="user",
                id=None,
            ),
            pagination=PaginationParams(
                page=1,
                page_size=10,
                offset=0,
            ),
            sort=SortParams(
                sort_by=PermissionSortField.NAME,
                sort_order=SortOrderField.ASC,
            ),
        )

        result: PaginatedResult[Permission] = await uow.permissions.get_list_by_filter(
            query
        )

        # باید فقط "user.read" و "user.write" را برگرداند
        names = [p.name for p in result.items]
        assert "user.read" in names
        assert "user.write" in names
        assert "admin.read" not in names
        assert result.total >= 2
        assert len(result.items) >= 2


@pytest.mark.asyncio
async def test_get_list_by_filter_with_pagination(uow: UnitOfWork):
    async with uow:
        # create multiple permissions
        for i in range(10):
            await uow.permissions.create(
                Permission(
                    id=None,
                    name=f"perm_{i}",
                )
            )

        query = FilterPermissionQuery(
            filters=None,
            pagination=PaginationParams(
                page=2,
                page_size=2,
                offset=5,
            ),
            sort=SortParams(
                sort_by=PermissionSortField.ID,
                sort_order=SortOrderField.ASC,
            ),
        )

        result: PaginatedResult[Permission] = await uow.permissions.get_list_by_filter(
            query
        )

        assert result.page == query.pagination.page
        assert result.page_size == query.pagination.page_size
        assert len(result.items) == query.pagination.page_size
        assert result.total >= 10
        names = [p.name for p in result.items]
        assert "perm_7" in names
        assert "perm_8" in names


@pytest.mark.asyncio
async def test_update_permission(uow: UnitOfWork):
    async with uow:
        perm = Permission(id=None, name="old_name")
        created = await uow.permissions.create(perm)

        created.name = "new_name"
        updated = await uow.permissions.update(created)

        assert updated.id == created.id
        assert updated.name == "new_name"

        # verify from DB
        fetched = await uow.permissions.get_or_raise(permission_id=created.safe_id)
        assert fetched.name == "new_name"


@pytest.mark.asyncio
async def test_update_permission_not_found_raises(uow: UnitOfWork):
    async with uow:
        fake_permission = Permission(id=999999, name="non_existing")

        with pytest.raises(PermissionNotFoundException):
            await uow.permissions.update(fake_permission)


@pytest.mark.asyncio
async def test_delete_permission(uow: UnitOfWork):
    async with uow:
        perm = Permission(id=None, name="to_be_deleted")
        created = await uow.permissions.create(perm)

        await uow.permissions.delete(permission_id=created.safe_id)

        fetched = await uow.permissions.get(permission_id=created.safe_id)
        assert fetched is None
