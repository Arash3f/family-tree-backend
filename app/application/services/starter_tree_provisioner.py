"""Create fully populated starter family trees for a new user."""

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.family_tree_sync_service import FamilyTreeSyncService
from app.domain.entities.family_tree import FamilyTree, TreeMemberRole, TreeMembership
from app.domain.entities.marriage import Marriage
from app.domain.entities.person import (
    Gender,
    ParentLink,
    ParentRelationshipType,
    Person,
)
from app.domain.services.marriage_rules import MarriageRulesService
from app.domain.shared.starter_tree_templates import (
    STARTER_TREE_TEMPLATES,
    StarterTreeTemplate,
)
from app.domain.shared.starter_trees import STARTER_TREE_SPECS, StarterTreeSpec
from app.domain.shared.tree_access import TreeAccessPermissions


@dataclass(slots=True)
class StarterProvisioningResult:
    trees: list[FamilyTree] = field(default_factory=list)
    persons: list[Person] = field(default_factory=list)
    marriages: list[Marriage] = field(default_factory=list)


class StarterTreeProvisioner:
    """Provisions starter trees inside an already-open UnitOfWork transaction."""

    def __init__(
        self,
        specs: tuple[StarterTreeSpec, ...] = STARTER_TREE_SPECS,
        sync_service: FamilyTreeSyncService | None = None,
    ):
        self._specs = specs
        self._sync_service = sync_service or FamilyTreeSyncService()

    async def provision_for_user(
        self, uow: UnitOfWork, *, owner_user_id: UUID
    ) -> StarterProvisioningResult:
        result = StarterProvisioningResult()
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
            persons, marriages = await self._populate_tree(
                uow,
                tree=tree,
                template=STARTER_TREE_TEMPLATES[spec.template_key],
            )
            result.trees.append(tree)
            result.persons.extend(persons)
            result.marriages.extend(marriages)
        return result

    async def _populate_tree(
        self,
        uow: UnitOfWork,
        *,
        tree: FamilyTree,
        template: StarterTreeTemplate,
    ) -> tuple[list[Person], list[Marriage]]:
        persons: list[Person] = []
        person_by_ref: dict[str, Person] = {}
        for person_row in template.persons:
            person = await uow.persons.create(
                Person(
                    id=None,
                    name=person_row.name,
                    family_name=person_row.family_name,
                    gender=Gender(person_row.gender),
                    tree_id=tree.safe_id,
                    birth_date=_optional_date(person_row.birth_date),
                    death_date=_optional_date(person_row.death_date),
                    birth_place=person_row.birth_place,
                    death_place=person_row.death_place,
                    notes=person_row.notes,
                )
            )
            persons.append(person)
            person_by_ref[person_row.ref] = person

        marriages: list[Marriage] = []
        marriage_by_ref: dict[str, Marriage] = {}
        for marriage_row in template.marriages:
            spouse_a = person_by_ref[marriage_row.spouse_a_ref]
            spouse_b = person_by_ref[marriage_row.spouse_b_ref]
            married_at = date.fromisoformat(marriage_row.married_at)
            MarriageRulesService.validate_marriage(
                spouse_a=spouse_a,
                spouse_b=spouse_b,
                marriage_date=married_at,
            )
            created_marriage = await uow.marriages.create(
                Marriage(
                    id=None,
                    tree_id=tree.safe_id,
                    spouse_a_id=spouse_a.safe_id,
                    spouse_b_id=spouse_b.safe_id,
                    married_at=married_at,
                    divorced_at=_optional_date(marriage_row.divorced_at),
                )
            )
            marriages.append(created_marriage)
            marriage_by_ref[marriage_row.ref] = created_marriage

        for person_row in template.persons:
            person = person_by_ref[person_row.ref]
            parent_links = [
                ParentLink(
                    parent_id=person_by_ref[parent_ref].safe_id,
                    relationship_type=ParentRelationshipType(
                        relationship_type or ParentRelationshipType.BIOLOGICAL
                    ),
                )
                for parent_ref, relationship_type in (
                    (person_row.parent1_ref, person_row.parent1_type),
                    (person_row.parent2_ref, person_row.parent2_type),
                )
                if parent_ref is not None
            ]
            linked_marriage = (
                marriage_by_ref[person_row.marriage_ref]
                if person_row.marriage_ref
                else None
            )
            if not parent_links and linked_marriage is None:
                continue
            person.set_parents(parent_links)
            person.marriage_id = (
                linked_marriage.safe_id if linked_marriage else None
            )
            person.validate()
            updated = await uow.persons.update(person=person)
            person_by_ref[person_row.ref] = updated

        return list(person_by_ref.values()), marriages

    def sync_after_commit(self, result: StarterProvisioningResult) -> None:
        """Enqueue graph writes only after the SQL transaction is durable."""
        for person in result.persons:
            self._sync_service.upsert_person(person)
        for marriage in result.marriages:
            if marriage.is_active():
                self._sync_service.upsert_spouse(
                    marriage.spouse_a_id,
                    marriage.spouse_b_id,
                )


def _optional_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None
