from abc import ABC, abstractmethod

from app.domain.entities.user import User
from app.domain.exceptions.user_exceptions import UserNotFoundException
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.user_filter_dto import FilterUserQuery
from app.domain.shared.dto.user_with_detail_dto import UserGetWithDetailResponseDTO


class UserRepository(ABC):
    """
    Repository contract for User persistence.

    This interface defines the operations required for working with
    User entities. The actual implementation is provided in the
    infrastructure layer.
    """

    @abstractmethod
    async def create(self, user: User) -> User: ...

    @abstractmethod
    async def get(self, user_id: int) -> User | None: ...

    @abstractmethod
    async def get_with_details(
        self, user_id: int
    ) -> UserGetWithDetailResponseDTO | None: ...

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    async def get_list_by_filter(
        self, query: FilterUserQuery
    ) -> PaginatedResult[User]: ...

    @abstractmethod
    async def update(self, user: User) -> User: ...

    @abstractmethod
    async def delete(self, user_id: int) -> None: ...

    async def get_or_raise(self, user_id: int) -> User:
        """
        Find a user by id or raise an exception if not found.

        Args:
            user_id:
                ID of the target user.

        Raises:
            UserNotFoundException:
                If no user exists with this id.
        """
        user = await self.get(user_id=user_id)

        if not user:
            raise UserNotFoundException(detail=[f"user id is {user_id}"])
        else:
            return user
