import pytest

from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.exceptions.role_exceptions import RoleNotFoundException
from app.domain.shared.dto.pagination_dto import PaginationParams
from app.domain.shared.dto.role_filter_dto import (
    FilterRoleQuery,
    RoleFilterDTO,
    RoleSortField,
)
from app.domain.shared.dto.sorter_dto import SortOrderField, SortParams


@pytest.mark.asyncio
async def test_create_and_get_role(uow: UnitOfWork):
    async with uow:
        perm = await uow.permissions.create(
            Permission(id=None, name="can_manage_users")
        )

        role = Role(
            id=None,
            name="admin",
            permission_ids=[perm.safe_id],
        )

        created = await uow.roles.create(role)
        fetched = await uow.roles.get(role_id=created.safe_id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "admin"
        assert perm.id in fetched.permission_ids


@pytest.mark.asyncio
async def test_get_or_raise_not_found(uow: UnitOfWork):
    async with uow:
        with pytest.raises(RoleNotFoundException):
            await uow.roles.get_or_raise(role_id=999999)


@pytest.mark.asyncio
async def test_get_by_name(uow: UnitOfWork):
    async with uow:
        role = Role(
            id=None,
            name="manager",
            permission_ids=[],
        )

        created = await uow.roles.create(role)

        fetched = await uow.roles.get_by_name("manager")

        assert fetched is not None
        assert fetched.id == created.id


@pytest.mark.asyncio
async def test_get_list_by_filter_with_name(uow: UnitOfWork):
    async with uow:
        await uow.roles.create(Role(id=None, name="admin", permission_ids=[]))
        await uow.roles.create(Role(id=None, name="super_admin", permission_ids=[]))
        await uow.roles.create(Role(id=None, name="user", permission_ids=[]))

        query = FilterRoleQuery(
            filters=RoleFilterDTO(
                name="admin",
            ),
            pagination=PaginationParams(
                page=1,
                page_size=10,
                offset=0,
            ),
            sort=SortParams(
                sort_by=RoleSortField.NAME,
                sort_order=SortOrderField.ASC,
            ),
        )

        result = await uow.roles.get_list_by_filter(query)

        names = [r.name for r in result.items]

        assert "admin" in names
        assert "super_admin" in names
        assert "user" not in names


@pytest.mark.asyncio
async def test_get_list_by_filter_with_permission_id(uow: UnitOfWork):
    async with uow:
        perm1 = await uow.permissions.create(Permission(id=None, name="perm1"))
        perm2 = await uow.permissions.create(Permission(id=None, name="perm2"))

        role1 = await uow.roles.create(
            Role(id=None, name="role1", permission_ids=[perm1.safe_id])
        )

        await uow.roles.create(
            Role(id=None, name="role2", permission_ids=[perm2.safe_id])
        )

        query = FilterRoleQuery(
            filters=RoleFilterDTO(
                permission_id=perm1.id,
            ),
            pagination=PaginationParams(page=1, page_size=10, offset=0),
            sort=SortParams(
                sort_by=RoleSortField.ID,
                sort_order=SortOrderField.ASC,
            ),
        )

        result = await uow.roles.get_list_by_filter(query)

        assert len(result.items) == 1
        assert result.items[0].id == role1.id


@pytest.mark.asyncio
async def test_update_role_permissions(uow: UnitOfWork):
    async with uow:
        perm1 = await uow.permissions.create(Permission(id=None, name="p1"))
        perm2 = await uow.permissions.create(Permission(id=None, name="p2"))

        role = await uow.roles.create(
            Role(id=None, name="role", permission_ids=[perm1.safe_id])
        )

        role.permission_ids = [perm2.safe_id]
        role.name = "updated_role"

        updated = await uow.roles.update(role)

        assert updated.name == "updated_role"
        assert perm2.id in updated.permission_ids
        assert perm1.id not in updated.permission_ids


@pytest.mark.asyncio
async def test_delete_role(uow: UnitOfWork):
    async with uow:
        role = await uow.roles.create(
            Role(id=None, name="to_delete", permission_ids=[])
        )

        await uow.roles.delete(role.safe_id)

        fetched = await uow.roles.get(role.safe_id)
        assert fetched is None


@pytest.mark.asyncio
async def test_role_name_duplicated_with_exception(uow: UnitOfWork):
    async with uow:
        role_1 = await uow.roles.create(Role(id=None, name="role_1", permission_ids=[]))
        role_2 = await uow.roles.create(Role(id=None, name="role_2", permission_ids=[]))

        result = await uow.roles.is_role_name_duplicated(
            role_name=role_1.name, exception_role_id=role_2.id
        )

        assert result is True


@pytest.mark.asyncio
async def test_role_name_duplicated(uow: UnitOfWork):
    async with uow:
        role_1 = await uow.roles.create(Role(id=None, name="role_1", permission_ids=[]))
        await uow.roles.create(Role(id=None, name="role_2", permission_ids=[]))

        result = await uow.roles.is_role_name_duplicated(role_name=role_1.name)

        assert result is True


@pytest.mark.asyncio
async def test_role_name_not_duplicated_with_exception(uow: UnitOfWork):
    async with uow:
        await uow.roles.create(Role(id=None, name="role_1", permission_ids=[]))
        role_2 = await uow.roles.create(Role(id=None, name="role_2", permission_ids=[]))

        result = await uow.roles.is_role_name_duplicated(
            role_name=role_2.name, exception_role_id=role_2.id
        )

        assert result is False


@pytest.mark.asyncio
async def test_role_name_not_duplicated(uow: UnitOfWork):
    async with uow:
        await uow.roles.create(Role(id=None, name="role_1", permission_ids=[]))

        result = await uow.roles.is_role_name_duplicated(role_name="test")

        assert result is False
