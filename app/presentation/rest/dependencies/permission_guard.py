from fastapi import Depends

from app.application.services.authorization_service import AuthorizationService
from app.domain.entities.user import User
from app.domain.exceptions.permission_exceptions import PermissionDeniedException
from app.presentation.rest.dependencies.auth_dependencies import get_current_user
from app.presentation.rest.utils.dependencies import get_authorization_service


class RequirePermission:
    def __init__(self, permission: str):
        self.permission = permission

    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        auth_service: AuthorizationService = Depends(get_authorization_service),
    ) -> User:
        has_permission = await auth_service.user_has_permission(
            current_user.safe_id,
            self.permission,
        )

        if not has_permission:
            raise PermissionDeniedException()

        return current_user


class RequireAnyPermission:
    def __init__(self, *permissions: str):
        self.permissions = permissions

    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        auth_service: AuthorizationService = Depends(get_authorization_service),
    ) -> User:
        has_permission = await auth_service.user_has_any_permission(
            current_user.safe_id,
            list(self.permissions),
        )
        if not has_permission:
            raise PermissionDeniedException()
        return current_user


class RequireAllPermissions:
    def __init__(self, *permissions: str):
        self.permissions = permissions

    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        auth_service: AuthorizationService = Depends(get_authorization_service),
    ) -> User:
        for permission in self.permissions:
            has_permission = await auth_service.user_has_permission(
                current_user.safe_id,
                permission,
            )
            if not has_permission:
                raise PermissionDeniedException()
        return current_user
