import pytest
from sqlalchemy import text

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.infrastructure.database.seed import seed_initial_permissions


@pytest.mark.asyncio
async def test_permission_seed_removes_stale_catalog_entries_and_role_links(uow):
    stale = await uow.permissions.create(
        Permission(id=None, name="person_create", description_en="", description_fa="")
    )
    await uow.roles.create(
        Role(name="legacy_genealogy_role", permission_ids=[stale.safe_id])
    )
    await uow.commit()

    await seed_initial_permissions(uow)

    assert await uow.permissions.get_by_name("person_create") is None
    remaining_links = await uow.session.scalar(
        text(
            """
            SELECT count(*)
            FROM role_permissions
            WHERE permission_id = :permission_id
            """
        ),
        {"permission_id": stale.safe_id},
    )
    assert remaining_links == 0
