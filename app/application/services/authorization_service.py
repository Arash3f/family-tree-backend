from app.application.services.unit_of_work import UnitOfWork


class AuthorizationService:
    """
    Service responsible for checking user permissions.

    This service encapsulates authorization logic and retrieves user data
    through the UnitOfWork pattern. It verifies whether a user has a specific
    permission or any permission from a given set based on the user's role.

    Attributes:
        uow (UnitOfWork): Unit of work instance used to access repositories
            and manage transactional boundaries.
    """

    def __init__(self, uow: UnitOfWork):
        """
        Initialize the authorization service.

        Args:
            uow (UnitOfWork): The unit of work used to retrieve user and role data.
        """
        self.uow = uow

    async def user_has_permission(
        self,
        user_id: int,
        permission_name: str,
    ) -> bool:
        """
        Check if a user has a specific permission.

        The method loads the user along with their role and permissions.
        If the user does not exist or has no assigned role, the result
        will be False.

        Args:
            user_id (int): Unique identifier of the user.
            permission_name (str): Name of the permission to check.

        Returns:
            bool: True if the user's role contains the given permission,
            otherwise False.
        """
        async with self.uow:
            user = await self.uow.users.get_with_details(user_id)

            if not user or not user.role:
                return False

            permission_names = {p.name for p in user.role.permissions}

            return permission_name in permission_names

    async def user_has_any_permission(
        self,
        user_id: int,
        permissions: list[str],
    ) -> bool:
        """
        Check if a user has at least one permission from a list.

        This method is useful when access can be granted by multiple
        alternative permissions.

        Args:
            user_id (int): Unique identifier of the user.
            permissions (list[str]): List of permission names to check.

        Returns:
            bool: True if the user has at least one of the given permissions,
            otherwise False.
        """
        async with self.uow:
            user = await self.uow.users.get_with_details(user_id)

            if not user or not user.role:
                return False

            permission_names = {p.name for p in user.role.permissions}

            return any(p in permission_names for p in permissions)
