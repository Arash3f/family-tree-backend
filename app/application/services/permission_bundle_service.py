from uuid import UUID

from app.domain.exceptions.permission_exceptions import PermissionNotFoundException
from app.domain.repositories.permission_repository import PermissionRepository
from app.domain.shared.permissions import Permissions


async def resolve_permission_ids_with_bundles(
    permissions: PermissionRepository,
    permission_ids: list[UUID],
) -> list[UUID]:
    """Validate IDs and auto-include mandatory companion permissions."""
    if not permission_ids:
        return []

    selected: list[tuple[UUID, str]] = []
    for permission_id in permission_ids:
        permission = await permissions.get_or_raise(permission_id=permission_id)
        selected.append((permission.safe_id, permission.name))

    selected_names = {name for _, name in selected}
    expanded_names = Permissions.expand_with_requirements(selected_names)
    missing_names = expanded_names - selected_names

    id_by_name = {name: permission_id for permission_id, name in selected}
    for name in missing_names:
        permission = await permissions.get_by_name(name)
        if permission is None:
            raise PermissionNotFoundException(detail=[f"permission name is {name}"])
        id_by_name[name] = permission.safe_id

    ordered: list[UUID] = []
    seen: set[UUID] = set()
    for permission_id, _ in selected:
        if permission_id not in seen:
            seen.add(permission_id)
            ordered.append(permission_id)
    for name in sorted(missing_names):
        permission_id = id_by_name[name]
        if permission_id not in seen:
            seen.add(permission_id)
            ordered.append(permission_id)
    return ordered
