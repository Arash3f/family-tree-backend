from collections.abc import Mapping
from enum import Enum
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.entities.user import User
from app.domain.exceptions.user_exceptions import UserNotFoundException
from app.domain.repositories.user_repository import UserRepository
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.user_filter_dto import FilterUserQuery, UserSortField
from app.infrastructure.database.models.role_model import RoleModel
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.database.utils.pagination_and_sort import paginate_and_sort
from app.domain.shared.dto.user_with_detail_dto import UserGetWithDetailResponseDTO


class SQLUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user: User) -> User:
        model = self._to_model(user)

        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)

        return self._to_entity(model)

    async def get(self, user_id: int) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id)

        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)

    async def get_with_details(
        self, user_id: int
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

        return UserGetWithDetailResponseDTO.from_model(model)

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

        return PaginatedResult[User](
            items=users,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )

    async def update(self, user: User) -> User:
        stmt = select(UserModel).where(UserModel.id == user.id)

        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            raise UserNotFoundException(detail=[f"user id is {user.id}"])

        model.username = user.username
        model.role_id = user.role_id
        model.password_hash = user.password_hash

        await self.session.flush()
        await self.session.refresh(model)

        return self._to_entity(model)

    async def delete(self, user_id: int) -> None:
        stmt = delete(UserModel).where(UserModel.id == user_id)

        await self.session.execute(stmt)

    def _to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            username=model.username,
            password_hash=model.password_hash,
            role_id=model.role_id,
        )

    def _to_model(self, entity: User) -> UserModel:
        model = UserModel(
            id=entity.id,
            username=entity.username,
            password_hash=entity.password_hash,
            role_id=entity.role_id,
        )

        return model
