from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.family_tree import FamilyTree, TreeMemberRole, TreeMembership
from app.domain.repositories.tree_repository import (
    TreeMembershipRepository,
    TreeRepository,
)
from app.domain.shared.tree_access import TreeAccessPermissions
from app.infrastructure.database.models.family_tree_model import FamilyTreeModel
from app.infrastructure.database.models.tree_membership_model import TreeMembershipModel


class SQLTreeRepository(TreeRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, tree: FamilyTree) -> FamilyTree:
        model = FamilyTreeModel(
            name=tree.name,
            owner_user_id=tree.owner_user_id,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get(self, tree_id: UUID) -> FamilyTree | None:
        stmt = select(FamilyTreeModel).where(FamilyTreeModel.id == tree_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_for_user(self, user_id: UUID) -> list[FamilyTree]:
        stmt = (
            select(FamilyTreeModel)
            .join(
                TreeMembershipModel,
                TreeMembershipModel.tree_id == FamilyTreeModel.id,
            )
            .where(TreeMembershipModel.user_id == user_id)
            .order_by(FamilyTreeModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_all(self) -> list[FamilyTree]:
        stmt = select(FamilyTreeModel).order_by(FamilyTreeModel.created_at.asc())
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count_owned_by_user(self, user_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(FamilyTreeModel)
            .where(FamilyTreeModel.owner_user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def update(self, tree: FamilyTree) -> FamilyTree:
        stmt = select(FamilyTreeModel).where(FamilyTreeModel.id == tree.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        model.name = tree.name
        model.owner_user_id = tree.owner_user_id
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def delete(self, tree_id: UUID) -> None:
        stmt = delete(FamilyTreeModel).where(FamilyTreeModel.id == tree_id)
        await self.session.execute(stmt)

    def _to_entity(self, model: FamilyTreeModel) -> FamilyTree:
        return FamilyTree(
            id=model.id,
            name=model.name,
            owner_user_id=model.owner_user_id,
        )


class SQLTreeMembershipRepository(TreeMembershipRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, membership: TreeMembership) -> TreeMembership:
        model = TreeMembershipModel(
            tree_id=membership.tree_id,
            user_id=membership.user_id,
            role=membership.role.value,
            permissions=TreeAccessPermissions.normalize(membership.permissions),
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get(self, tree_id: UUID, user_id: UUID) -> TreeMembership | None:
        stmt = select(TreeMembershipModel).where(
            TreeMembershipModel.tree_id == tree_id,
            TreeMembershipModel.user_id == user_id,
            TreeMembershipModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_tree(self, tree_id: UUID) -> list[TreeMembership]:
        stmt = (
            select(TreeMembershipModel)
            .where(
                TreeMembershipModel.tree_id == tree_id,
                TreeMembershipModel.deleted_at.is_(None),
            )
            .order_by(TreeMembershipModel.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_tree_with_usernames(
        self, tree_id: UUID
    ) -> list[tuple[TreeMembership, str | None]]:
        from app.infrastructure.database.models.user_model import UserModel

        stmt = (
            select(TreeMembershipModel, UserModel.username)
            .outerjoin(UserModel, UserModel.id == TreeMembershipModel.user_id)
            .where(
                TreeMembershipModel.tree_id == tree_id,
                TreeMembershipModel.deleted_at.is_(None),
            )
            .order_by(TreeMembershipModel.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return [(self._to_entity(m), username) for m, username in result.all()]

    async def list_by_user(self, user_id: UUID) -> list[TreeMembership]:
        stmt = select(TreeMembershipModel).where(
            TreeMembershipModel.user_id == user_id,
            TreeMembershipModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count_owners(self, tree_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(TreeMembershipModel)
            .where(
                TreeMembershipModel.tree_id == tree_id,
                TreeMembershipModel.role == TreeMemberRole.OWNER.value,
                TreeMembershipModel.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def update(self, membership: TreeMembership) -> TreeMembership:
        stmt = select(TreeMembershipModel).where(
            TreeMembershipModel.tree_id == membership.tree_id,
            TreeMembershipModel.user_id == membership.user_id,
            TreeMembershipModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        model.role = membership.role.value
        model.permissions = TreeAccessPermissions.normalize(membership.permissions)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def delete(self, tree_id: UUID, user_id: UUID) -> None:
        stmt = (
            update(TreeMembershipModel)
            .where(
                TreeMembershipModel.tree_id == tree_id,
                TreeMembershipModel.user_id == user_id,
                TreeMembershipModel.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)

    def _to_entity(self, model: TreeMembershipModel) -> TreeMembership:
        raw = model.permissions if isinstance(model.permissions, list) else []
        return TreeMembership(
            id=model.id,
            tree_id=model.tree_id,
            user_id=model.user_id,
            role=TreeMemberRole(model.role),
            permissions=TreeAccessPermissions.normalize(raw),
        )
