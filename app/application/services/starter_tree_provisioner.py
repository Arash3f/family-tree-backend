"""Create the starter family trees owned by a newly registered user.

Structure only for now: empty trees + owner membership. Template population
(people, marriages, Neo4j sync) will plug into `_populate_tree` later.
"""

from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.family_tree import FamilyTree, TreeMemberRole, TreeMembership
from app.domain.shared.starter_trees import STARTER_TREE_SPECS, StarterTreeSpec
from app.domain.shared.tree_access import TreeAccessPermissions


class StarterTreeProvisioner:
    """Provisions starter trees inside an already-open UnitOfWork transaction."""

    def __init__(self, specs: tuple[StarterTreeSpec, ...] = STARTER_TREE_SPECS):
        self._specs = specs

    async def provision_for_user(
        self, uow: UnitOfWork, *, owner_user_id: UUID
    ) -> list[FamilyTree]:
        trees: list[FamilyTree] = []
        for spec in self._specs:
            tree = await uow.family_trees.create(
                FamilyTree(
                    id=None,
                    name=spec.default_name,
                    owner_user_id=owner_user_id,
                )
            )
            await uow.tree_memberships.create(
                TreeMembership(
                    id=None,
                    tree_id=tree.safe_id,
                    user_id=owner_user_id,
                    role=TreeMemberRole.OWNER,
                    permissions=list(TreeAccessPermissions.ALL),
                )
            )
            await self._populate_tree(uow, tree=tree, spec=spec)
            trees.append(tree)
        return trees

    async def _populate_tree(
        self,
        uow: UnitOfWork,
        *,
        tree: FamilyTree,
        spec: StarterTreeSpec,
    ) -> None:
        """Hook for seeding persons/relationships from `spec.template_key`.

        No-op until templates are defined.
        """
        _ = (uow, tree, spec)
