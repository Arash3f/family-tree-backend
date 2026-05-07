from abc import ABC, abstractmethod

from app.domain.entities.role import Role
from app.domain.exceptions.role_exceptions import RoleNotFoundException
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.role_filter_dto import FilterRoleQuery


class RoleRepository(ABC):
    """
    Repository contract for Role persistence.

    This interface defines the operations required for working with
    Role entities. The actual implementation is provided in the
    infrastructure layer.
    """

    @abstractmethod
    async def create(self, role: Role) -> Role: ...

    @abstractmethod
    async def get(self, role_id: int) -> Role | None: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Role | None: ...

    @abstractmethod
    async def get_list_by_filter(
        self, query: FilterRoleQuery
    ) -> PaginatedResult[Role]: ...

    @abstractmethod
    async def update(self, role: Role) -> Role: ...

    @abstractmethod
    async def delete(self, role_id: int) -> None: ...

    async def get_or_raise(self, role_id: int) -> Role:
        """
        Find a role by id or raise an exception if not found.

        Args:
            role_id:
                ID of the target role.

        Raises:
            RoleNotFoundException:
                If no role exists with this id.
        """
        role = await self.get(role_id=role_id)

        if not role:
            raise RoleNotFoundException(detail=[f"role id is {role_id}"])
        else:
            return role
