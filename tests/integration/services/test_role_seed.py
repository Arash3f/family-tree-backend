import pytest

from app.core.config import settings
from app.domain.shared.permissions import Permissions
from app.infrastructure.database.seed import (
    MEMBER_ROLE_PERMISSIONS,
    seed_initial_permissions,
    seed_initial_roles,
)


@pytest.mark.asyncio
async def test_seed_initial_roles_creates_admin_and_member(uow):
    await seed_initial_permissions(uow)
    admin_role, member_role = await seed_initial_roles(uow)

    assert admin_role.name == settings.ADMIN_ROLE_NAME
    assert member_role.name == settings.MEMBER_ROLE_NAME

    all_permission_ids = {p.safe_id for p in await uow.permissions.get_list()}
    assert set(admin_role.permission_ids) == all_permission_ids

    expected_member = set(Permissions.expand_with_requirements(MEMBER_ROLE_PERMISSIONS))
    member_names = {
        (await uow.permissions.get_or_raise(permission_id=pid)).name
        for pid in member_role.permission_ids
    }
    assert member_names == expected_member

    # Idempotent: second run keeps the same built-in roles.
    again_admin, again_member = await seed_initial_roles(uow)
    assert again_admin.safe_id == admin_role.safe_id
    assert again_member.safe_id == member_role.safe_id
