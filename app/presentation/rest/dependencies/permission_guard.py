from fastapi import Depends

from app.application.services.authorization_service import AuthorizationService
from app.domain.exceptions.permission_exceptions import PermissionDeniedException
from app.presentation.rest.dependencies.auth_dependencies import get_current_user
from app.presentation.rest.utils.dependencies import get_authorization_service


class RequirePermission:
    def __init__(self, permission: str):
        self.permission = permission

    async def __call__(
        self,
        current_user=Depends(get_current_user),
        auth_service: AuthorizationService = Depends(get_authorization_service),
    ):
        has_permission = await auth_service.user_has_permission(
            current_user.id,
            self.permission,
        )

        if not has_permission:
            raise PermissionDeniedException()
