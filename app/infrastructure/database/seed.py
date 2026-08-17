from app.application.interfaces.unit_of_work import UnitOfWork
from app.core.config import settings
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.domain.shared.account_type import AccountType
from app.infrastructure.services.security.password_hasher_impl import (
    Argon2PasswordHasher,
)
from app.domain.shared.permissions import Permissions


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
                account_type=AccountType.PAID,
            )
            await uow.users.create(user)
        else:
            changed = False
            if admin.role_id:
                admin_role = await uow.roles.get_or_raise(role_id=admin.role_id)
                if admin_role.name != settings.ADMIN_ROLE_NAME:
                    admin.role_id = role.safe_id
                    changed = True
            else:
                admin.role_id = role.safe_id
                changed = True
            if admin.account_type is not AccountType.PAID:
                admin.account_type = AccountType.PAID
                changed = True
            if changed:
                await uow.users.update(admin)

        await uow.commit()


async def seed_initial_permissions(uow: UnitOfWork):
    async with uow:
        catalog = set(Permissions.get_all_permissions())
        for perm_name in catalog:
            description_en, description_fa = Permissions.get_descriptions(perm_name)
            permission = await uow.permissions.get_by_name(perm_name)
            if not permission:
                await uow.permissions.create(
                    Permission(
                        name=perm_name,
                        description_en=description_en,
                        description_fa=description_fa,
                    )
                )
            elif (
                permission.description_en != description_en
                or permission.description_fa != description_fa
            ):
                permission.description_en = description_en
                permission.description_fa = description_fa
                await uow.permissions.update(permission)

        for permission in await uow.permissions.get_list():
            if permission.name not in catalog:
                await uow.permissions.delete(permission.safe_id)

        await uow.commit()
