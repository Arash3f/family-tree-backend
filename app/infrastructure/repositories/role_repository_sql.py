from collections.abc import Mapping
from enum import Enum
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.role import Role
from app.domain.repositories.role_repository import RoleRepository
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.role_filter_dto import FilterRoleQuery, RoleSortField
from app.infrastructure.database.models.permission_model import PermissionModel
from app.infrastructure.database.models.role_model import RoleModel
from app.infrastructure.database.utils.pagination_and_sort import paginate_and_sort


class SQLRoleRepository(RoleRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, role: Role) -> Role:
        stmt_permissions = select(PermissionModel).where(
            PermissionModel.id.in_(role.permission_ids)
        )
        result_permissions = await self.session.execute(stmt_permissions)
        permissions = list(result_permissions.scalars().all())

        model = RoleModel(
            name=role.name,
            permissions=permissions,
        )

        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)

        return self._to_entity(model)

    async def get(self, role_id: int) -> Role | None:
        stmt = select(RoleModel).where(RoleModel.id == role_id)

        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)

    async def get_by_name(self, name: str) -> Role | None:
        stmt = select(RoleModel).where(RoleModel.name == name)

        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)

    async def get_list_by_filter(self, query: FilterRoleQuery) -> PaginatedResult[Role]:
        stmt = select(RoleModel)
        filters = query.filters

        if filters:
            if filters.name:
                stmt = stmt.where(RoleModel.name.ilike(f"%{filters.name}%"))

            if filters.id:
                stmt = stmt.where(RoleModel.id.ilike(f"%{filters.id}%"))

            if filters.permission_id is not None:
                stmt = stmt.join(RoleModel.permissions).where(
                    PermissionModel.id == filters.permission_id
                )

        SORTABLE_COLUMNS: Mapping[Enum, Any] = {
            RoleSortField.ID: RoleModel.id,
            RoleSortField.NAME: RoleModel.name,
        }

        result = await paginate_and_sort(
            model=RoleModel,
            stmt=stmt,
            session=self.session,
            page=query.pagination.page,
            page_size=query.pagination.page_size,
            sort_by=query.sort.sort_by,
            offset=query.pagination.offset,
            sort_order=query.sort.sort_order,
            sortable_columns=SORTABLE_COLUMNS,
        )

        roles = [self._to_entity(m) for m in result.items]

        return PaginatedResult[Role](
            items=roles,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )

    async def update(self, role: Role) -> Role:
        stmt = select(RoleModel).where(RoleModel.id == role.id)

        result = await self.session.execute(stmt)
        model = result.unique().scalar_one()

        # Get all permissions:
        stmt_permissions = select(PermissionModel).where(
            PermissionModel.id.in_(role.permission_ids)
        )
        result_permissions = await self.session.execute(stmt_permissions)
        permissions = list(result_permissions.scalars().all())

        # Update data
        model.name = role.name
        model.permissions = permissions

        await self.session.flush()
        await self.session.refresh(model)

        return self._to_entity(model)

    async def delete(self, role_id: int) -> None:
        stmt = delete(RoleModel).where(RoleModel.id == role_id)

        await self.session.execute(stmt)

    def _to_entity(self, model: RoleModel) -> Role:
        permission_ids = [p.id for p in model.permissions]
        return Role(
            id=model.id,
            name=model.name,
            permission_ids=permission_ids,
        )

    def _to_model(self, entity: Role) -> RoleModel:
        model = RoleModel(
            id=entity.id,
            name=entity.name,
            permissions=entity.permission_ids,
        )

        return model
