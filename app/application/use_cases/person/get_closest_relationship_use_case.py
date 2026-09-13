import asyncio
from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.exceptions.person_exceptions import PersonNotFoundException
from app.domain.repositories.family_tree_repository import FamilyTreeRepository
from app.domain.services.relationship_path_diversity import path_hops_for_tree_size
from app.domain.shared.dto.family_tree_dto import PersonIdDTO, RelationshipPathDTO


async def _ensure_persons_and_max_hops(
    family_tree_repo: FamilyTreeRepository,
    from_person_id: UUID,
    to_person_id: UUID,
    *,
    tree_id: UUID,
    uow: UnitOfWork | None,
) -> tuple[int | None, int | None]:
    """Validate endpoints; return (person_count, max_hops) when PG size is known.

    When ``uow`` is missing, both values are ``None`` so the Neo4j repository
    can size the hop budget from the graph itself.
    """
    person_count: int | None = None
    if uow is not None:
        async with uow:
            await uow.persons.get_in_tree_or_raise(
                person_id=from_person_id, tree_id=tree_id
            )
            await uow.persons.get_in_tree_or_raise(
                person_id=to_person_id, tree_id=tree_id
            )
            person_count = await uow.persons.count_in_tree(tree_id)

    from_exists, to_exists = await asyncio.gather(
        family_tree_repo.person_exists(PersonIdDTO(id=from_person_id), tree_id=tree_id),
        family_tree_repo.person_exists(PersonIdDTO(id=to_person_id), tree_id=tree_id),
    )

    if not from_exists:
        raise PersonNotFoundException(
            detail=[f"person {from_person_id} not found in graph"]
        )

    if not to_exists:
        raise PersonNotFoundException(
            detail=[f"person {to_person_id} not found in graph"]
        )

    if person_count is None:
        return None, None
    return person_count, path_hops_for_tree_size(person_count)


class GetClosestRelationshipUseCase:
    """Return only the shortest kinship path (fast path for the first request)."""

    def __init__(
        self,
        family_tree_repo: FamilyTreeRepository,
        uow: UnitOfWork | None = None,
    ):
        self.family_tree_repo = family_tree_repo
        self.uow = uow

    async def execute(
        self,
        from_person_id: UUID,
        to_person_id: UUID,
        *,
        tree_id: UUID,
        male_only: bool = False,
    ) -> RelationshipPathDTO:
        person_count, max_hops = await _ensure_persons_and_max_hops(
            self.family_tree_repo,
            from_person_id,
            to_person_id,
            tree_id=tree_id,
            uow=self.uow,
        )
        return await self.family_tree_repo.find_shortest_relationship_path(
            from_person_id=from_person_id,
            to_person_id=to_person_id,
            tree_id=tree_id,
            max_hops=max_hops,
            person_count=person_count,
            male_only=male_only,
        )


class GetAlternativeRelationshipPathsUseCase:
    """Return diverse alternative routes; intended as a follow-up request."""

    def __init__(
        self,
        family_tree_repo: FamilyTreeRepository,
        uow: UnitOfWork | None = None,
    ):
        self.family_tree_repo = family_tree_repo
        self.uow = uow

    async def execute(
        self,
        from_person_id: UUID,
        to_person_id: UUID,
        *,
        tree_id: UUID,
        male_only: bool = False,
    ) -> RelationshipPathDTO:
        person_count, max_hops = await _ensure_persons_and_max_hops(
            self.family_tree_repo,
            from_person_id,
            to_person_id,
            tree_id=tree_id,
            uow=self.uow,
        )
        return await self.family_tree_repo.find_diverse_relationship_paths(
            from_person_id=from_person_id,
            to_person_id=to_person_id,
            tree_id=tree_id,
            max_hops=max_hops,
            person_count=person_count,
            male_only=male_only,
        )
