from app.application.services.unit_of_work import UnitOfWork


class AuthorizationService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def user_has_permission(
        self,
        user_id: int,
        permission_name: str,
    ) -> bool:
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
        async with self.uow:
            user = await self.uow.users.get_with_details(user_id)

            if not user or not user.role:
                return False

            permission_names = {p.name for p in user.role.permissions}

            return any(p in permission_names for p in permissions)
