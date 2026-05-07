from collections.abc import Mapping
from enum import Enum
from typing import Any, List

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.permission import Permission
from app.domain.exceptions.permission_exceptions import PermissionNotFoundException
from app.domain.repositories.permission_repository import PermissionRepository
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.permission_filter_dto import (
    FilterPermissionQuery,
    PermissionSortField,
)
from app.infrastructure.database.models.permission_model import PermissionModel
from app.infrastructure.database.utils.pagination_and_sort import paginate_and_sort


class SQLPermissionRepository(PermissionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, permission: Permission) -> Permission:
        model = self._to_model(permission)

        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)

        return self._to_entity(model)

    async def get(self, permission_id: int) -> Permission | None:
        stmt = select(PermissionModel).where(PermissionModel.id == permission_id)

        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)

    async def get_by_name(self, name: str) -> Permission | None:
        stmt = select(PermissionModel).where(PermissionModel.name == name)

        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)

    async def get_list(self) -> List[Permission]:
        exec = await self.session.execute(select(PermissionModel))
        result = exec.scalars()
        permissions = [self._to_entity(m) for m in result]
        return permissions

    async def get_list_by_filter(
        self, query: FilterPermissionQuery
    ) -> PaginatedResult[Permission]:
        stmt = select(PermissionModel)
        filters = query.filters

        if filters:
            if filters.name:
                stmt = stmt.where(PermissionModel.name.ilike(f"%{filters.name}%"))

            if filters.id:
                stmt = stmt.where(PermissionModel.id == filters.id)

        SORTABLE_COLUMNS: Mapping[Enum, Any] = {
            PermissionSortField.ID: PermissionModel.id,
            PermissionSortField.NAME: PermissionModel.name,
        }

        result = await paginate_and_sort(
            model=PermissionModel,
            stmt=stmt,
            session=self.session,
            page=query.pagination.page,
            offset=query.pagination.offset,
            page_size=query.pagination.page_size,
            sort_by=query.sort.sort_by,
            sort_order=query.sort.sort_order,
            sortable_columns=SORTABLE_COLUMNS,
        )

        permissions = [self._to_entity(m) for m in result.items]

        return PaginatedResult[Permission](
            items=permissions,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )

    async def update(self, permission: Permission) -> Permission:
        stmt = select(PermissionModel).where(PermissionModel.id == permission.id)

        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            raise PermissionNotFoundException(
                detail=[f"permission id is {permission.id}"]
            )

        model.name = permission.name

        await self.session.flush()
        await self.session.refresh(model)

        return self._to_entity(model)

    async def delete(self, permission_id: int) -> None:
        stmt = delete(PermissionModel).where(PermissionModel.id == permission_id)

        await self.session.execute(stmt)

    def _to_entity(self, model: PermissionModel) -> Permission:
        return Permission(
            id=model.id,
            name=model.name,
        )

    def _to_model(self, entity: Permission) -> PermissionModel:
        model = PermissionModel(
            id=entity.id,
            name=entity.name,
        )

        return model
