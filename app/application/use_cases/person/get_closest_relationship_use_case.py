import asyncio
from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.exceptions.person_exceptions import PersonNotFoundException
from app.domain.repositories.family_tree_repository import FamilyTreeRepository
from app.domain.shared.dto.family_tree_dto import PersonIdDTO, RelationshipPathDTO


class GetClosestRelationshipUseCase:
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
    ) -> RelationshipPathDTO:
        if self.uow is not None:
            async with self.uow:
                await self.uow.persons.get_in_tree_or_raise(
                    person_id=from_person_id, tree_id=tree_id
                )
                await self.uow.persons.get_in_tree_or_raise(
                    person_id=to_person_id, tree_id=tree_id
                )

        from_exists, to_exists = await asyncio.gather(
            self.family_tree_repo.person_exists(
                PersonIdDTO(id=from_person_id), tree_id=tree_id
            ),
            self.family_tree_repo.person_exists(
                PersonIdDTO(id=to_person_id), tree_id=tree_id
            ),
        )

        if not from_exists:
            raise PersonNotFoundException(
                detail=[f"person {from_person_id} not found in graph"]
            )

        if not to_exists:
            raise PersonNotFoundException(
                detail=[f"person {to_person_id} not found in graph"]
            )

        return await self.family_tree_repo.find_shortest_relationship_path(
            from_person_id=from_person_id,
            to_person_id=to_person_id,
            tree_id=tree_id,
        )
