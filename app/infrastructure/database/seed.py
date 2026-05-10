from app.application.services.unit_of_work import UnitOfWork
from app.core.config import settings
from app.domain.constants.permissions import Permissions
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.infrastructure.security.password_hasher_impl import Argon2PasswordHasher

permissions = [
    # User:
    Permission(name="create_user"),
    Permission(name="delete_user"),
    Permission(name="get_user"),
    Permission(name="update_user"),
    # Role:
    Permission(name="create_role"),
    Permission(name="delete_role"),
    Permission(name="get_role"),
    Permission(name="update_role"),
    # Permission:
    Permission(name="get_permission"),
    # Marriage:
    Permission(name="create_marriage"),
    Permission(name="delete_marriage"),
    Permission(name="divorce_marriage"),
    Permission(name="get_marriage"),
    Permission(name="update_marriage"),
    # Person:
    Permission(name="create_person"),
    Permission(name="delete_person"),
    Permission(name="get_person"),
    Permission(name="update_person"),
]


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
        permissions = [
            # User:
            Permission(name=Permissions.USER_CREATE),
            Permission(name=Permissions.USER_DELETE),
            Permission(name=Permissions.USER_READ),
            Permission(name=Permissions.USER_UPDATE),
            # Role:
            Permission(name=Permissions.ROLE_CREATE),
            Permission(name=Permissions.ROLE_DELETE),
            Permission(name=Permissions.ROLE_READ),
            Permission(name=Permissions.ROLE_UPDATE),
            # Permission:
            Permission(name=Permissions.PERMISSION_READ),
            # Marriage:
            Permission(name=Permissions.MARRIAGE_CREATE),
            Permission(name=Permissions.MARRIAGE_READ),
            Permission(name=Permissions.MARRIAGE_UPDATE),
            Permission(name=Permissions.MARRIAGE_DELETE),
            Permission(name=Permissions.MARRIAGE_DIVORCE),
            # Person:
            Permission(name=Permissions.PERSON_CREATE),
            Permission(name=Permissions.PERSON_READ),
            Permission(name=Permissions.PERSON_UPDATE),
            Permission(name=Permissions.PERSON_DELETE),
        ]
        for perm in permissions:
            permission = await uow.permissions.get_by_name(perm.name)
            if not permission:
                await uow.permissions.create(perm)

        await uow.commit()
