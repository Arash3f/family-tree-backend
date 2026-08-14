from uuid import UUID, uuid4

from app.application.interfaces.unit_of_work import UnitOfWork
from app.core.config import settings
from app.domain.entities.family_tree import FamilyTree, TreeMemberRole, TreeMembership
from app.domain.entities.user import User
from app.domain.shared.tree_access import TreeAccessPermissions


async def get_admin_user(uow: UnitOfWork) -> User:
    admin = await uow.users.get_by_username(settings.ADMIN_USERNAME)
    if not admin:
        raise RuntimeError(
            f"Admin user {settings.ADMIN_USERNAME!r} not found; run seed_initial_user"
        )
    return admin


async def create_family_tree_with_owner(
    uow: UnitOfWork,
    *,
    owner: User | None = None,
    name: str | None = None,
) -> FamilyTree:
    if owner is None:
        owner = User(username=f"owner_{uuid4().hex[:12]}", password_hash="hash")
        owner = await uow.users.create(owner)

    tree = await uow.family_trees.create(
        FamilyTree(
            id=None,
            name=name or f"Tree {uuid4().hex[:8]}",
            owner_user_id=owner.safe_id,
        )
    )
    await uow.tree_memberships.create(
        TreeMembership(
            id=None,
            tree_id=tree.safe_id,
            user_id=owner.safe_id,
            role=TreeMemberRole.OWNER,
            permissions=list(TreeAccessPermissions.ALL),
        )
    )
    return tree


async def add_tree_member(
    uow: UnitOfWork,
    *,
    tree_id: UUID,
    user_id: UUID,
    role: TreeMemberRole = TreeMemberRole.MEMBER,
    permissions: list[str] | None = None,
) -> TreeMembership:
    membership = await uow.tree_memberships.create(
        TreeMembership(
            id=None,
            tree_id=tree_id,
            user_id=user_id,
            role=role,
            permissions=permissions
            or (
                list(TreeAccessPermissions.ALL)
                if role is TreeMemberRole.OWNER
                else [TreeAccessPermissions.VIEW]
            ),
        )
    )
    return membership
