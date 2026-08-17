from collections.abc import Mapping
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.entities.user import User
from app.domain.exceptions.user_exceptions import UserNotFoundException
from app.domain.repositories.user_repository import UserRepository
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.user_filter_dto import FilterUserQuery, UserSortField
from app.domain.shared.dto.user_with_detail_dto import UserGetWithDetailResponseDTO
from app.infrastructure.database.models.associations import role_permissions
from app.infrastructure.database.models.permission_model import PermissionModel
from app.infrastructure.database.models.role_model import RoleModel
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.database.models.user_session_model import UserSessionModel
from app.infrastructure.database.utils.pagination_and_sort import paginate_and_sort
from app.infrastructure.mappers.user_detail_mapper import user_model_to_detail_dto


class SQLUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user: User) -> User:
        model = self._to_model(user)

        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)

        return self._to_entity(model)

    async def get(self, user_id: UUID) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id)

        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)

    async def get_for_update(self, user_id: UUID) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id).with_for_update()
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_with_details(
        self, user_id: UUID
    ) -> UserGetWithDetailResponseDTO | None:
        stmt = (
            select(UserModel)
            .where(UserModel.id == user_id)
            .options(joinedload(UserModel.role).joinedload(RoleModel.permissions))
        )

        result = await self.session.execute(stmt)

        model = result.unique().scalar_one_or_none()

        if model is None:
            return None

        return user_model_to_detail_dto(model)

    async def ids_having_permission(
        self, user_ids: list[UUID], permission_name: str
    ) -> set[UUID]:
        if not user_ids:
            return set()

        stmt = (
            select(UserModel.id)
            .join(RoleModel, UserModel.role_id == RoleModel.id)
            .join(role_permissions, role_permissions.c.role_id == RoleModel.id)
            .join(
                PermissionModel,
                PermissionModel.id == role_permissions.c.permission_id,
            )
            .where(UserModel.id.in_(user_ids))
            .where(PermissionModel.name == permission_name)
        )
        result = await self.session.execute(stmt)
        return set(result.scalars().all())

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(UserModel).where(UserModel.username == username)

        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)

    async def get_list_by_filter(self, query: FilterUserQuery) -> PaginatedResult[User]:
        stmt = select(UserModel)
        filters = query.filters

        if filters:
            if filters.username:
                stmt = stmt.where(UserModel.username.ilike(f"%{filters.username}%"))

            if filters.id:
                stmt = stmt.where(UserModel.id == filters.id)

            if filters.role_id:
                stmt = stmt.where(UserModel.role_id == filters.role_id)

        SORTABLE_COLUMNS: Mapping[Enum, Any] = {
            UserSortField.ID: UserModel.id,
            UserSortField.USERNAME: UserModel.username,
            UserSortField.ROLE_ID: UserModel.role_id,
        }

        result = await paginate_and_sort(
            model=UserModel,
            stmt=stmt,
            session=self.session,
            page=query.pagination.page,
            page_size=query.pagination.page_size,
            sort_by=query.sort.sort_by,
            offset=query.pagination.offset,
            sort_order=query.sort.sort_order,
            sortable_columns=SORTABLE_COLUMNS,
        )

        users = [self._to_entity(m) for m in result.items]
        await self._attach_last_session_at(users)

        return PaginatedResult[User](
            items=users,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )

    async def _attach_last_session_at(self, users: list[User]) -> None:
        user_ids = [user.safe_id for user in users if user.id is not None]
        if not user_ids:
            return

        stmt = (
            select(
                UserSessionModel.user_id,
                func.max(UserSessionModel.created_at),
            )
            .where(UserSessionModel.user_id.in_(user_ids))
            .group_by(UserSessionModel.user_id)
        )
        rows = await self.session.execute(stmt)
        last_by_user = {user_id: created_at for user_id, created_at in rows.all()}

        for user in users:
            if user.id is not None:
                user.last_session_at = last_by_user.get(user.id)

    async def update(self, user: User) -> User:
        stmt = select(UserModel).where(UserModel.id == user.id)

        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            raise UserNotFoundException(detail=[f"user id is {user.id}"])

        model.username = user.username
        model.fullname = user.fullname
        model.role_id = user.role_id
        model.password_hash = user.password_hash
        model.account_type = user.account_type.value

        await self.session.flush()
        await self.session.refresh(model)

        return self._to_entity(model)

    async def delete(self, user_id: UUID) -> None:
        stmt = delete(UserModel).where(UserModel.id == user_id)

        await self.session.execute(stmt)

    def _to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            username=model.username,
            fullname=model.fullname,
            password_hash=model.password_hash,
            role_id=model.role_id,
            account_type=model.account_type,
        )

    def _to_model(self, entity: User) -> UserModel:
        model = UserModel(
            id=entity.id,
            username=entity.username,
            fullname=entity.fullname,
            password_hash=entity.password_hash,
            role_id=entity.role_id,
            account_type=entity.account_type.value,
        )

        return model
