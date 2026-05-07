from abc import ABC, abstractmethod
from typing import List

from app.domain.entities.permission import Permission
from app.domain.exceptions.permission_exceptions import PermissionNotFoundException
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.permission_filter_dto import FilterPermissionQuery


class PermissionRepository(ABC):
    """
    Repository contract for Permission persistence.

    This interface defines the operations required for working with
    Permission entities. The actual implementation is provided in the
    infrastructure layer.
    """

    @abstractmethod
    async def create(self, permission: Permission) -> Permission: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Permission | None: ...

    @abstractmethod
    async def get(self, permission_id: int) -> Permission | None: ...

    @abstractmethod
    async def get_list_by_filter(
        self, query: FilterPermissionQuery
    ) -> PaginatedResult[Permission]: ...

    @abstractmethod
    async def get_list(self) -> List[Permission]: ...

    @abstractmethod
    async def update(self, permission: Permission) -> Permission: ...

    @abstractmethod
    async def delete(self, permission_id: int) -> None: ...

    async def get_or_raise(self, permission_id: int) -> Permission:
        """
        Find a permission by id or raise an exception if not found.

        Args:
            permission_id:
                ID of the target permission.

        Raises:
            PermissionNotFoundException:
                If no permission exists with this id.
        """
        permission = await self.get(permission_id=permission_id)

        if not permission:
            raise PermissionNotFoundException(
                detail=[f"permission id is {permission_id}"]
            )
        else:
            return permission
