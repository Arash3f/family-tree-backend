from app.application.interfaces.unit_of_work import UnitOfWork
from app.core.config import settings
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.infrastructure.services.security.password_hasher_impl import (
    Argon2PasswordHasher,
)
from app.infrastructure.utils.constants.permissions import Permissions


async def seed_initial_user(uow: UnitOfWork, password_hasher: Argon2PasswordHasher):
    async with uow:
        admin = await uow.users.get_by_username(settings.ADMIN_USERNAME)
        role = await uow.roles.get_by_name(settings.ADMIN_ROLE_NAME)
        permissions = await uow.permissions.get_list()

        if not role:
            role = Role(
                name=settings.ADMIN_ROLE_NAME,
                permission_ids=[perm.safe_id for perm in permissions],
            )
            role = await uow.roles.create(role)
        else:
            role.permission_ids = [perm.safe_id for perm in permissions]
            await uow.roles.update(role)

        if not admin:
            hashed_password = password_hasher.hash(settings.ADMIN_PASSWORD)

            user = User(
                username=settings.ADMIN_USERNAME,
                role_id=role.safe_id,
                password_hash=hashed_password,
            )
            await uow.users.create(user)
        elif admin.role_id:
            admin_role = await uow.roles.get_or_raise(role_id=admin.role_id)
            if admin_role.name != settings.ADMIN_ROLE_NAME:
                admin.role_id = role.id
        else:
            admin.role_id = role.id

        await uow.commit()


async def seed_initial_permissions(uow: UnitOfWork):
    async with uow:
        for perm_name in Permissions.get_all_permissions():
            permission = await uow.permissions.get_by_name(perm_name)
            if not permission:
                perm = Permission(name=perm_name)
                await uow.permissions.create(perm)

        await uow.commit()
