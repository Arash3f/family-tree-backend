from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.application.dto.marriage.marriage_create_dto import (
    MarriageCreateDTO,
    MarriageCreateMapper,
    MarriageCreateResponseDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.family_tree_sync_service import FamilyTreeSyncService
from app.domain.entities.marriage import Marriage
from app.domain.exceptions.family_tree_exceptions import MarriageTreeMismatchException
from app.domain.services.marriage_rules import MarriageRulesService


class CreateMarriageUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        marriage_rules_service: MarriageRulesService,
        sync_service: FamilyTreeSyncService | None = None,
    ):
        self.uow = uow
        self.marriage_rules_service = marriage_rules_service
        self.sync_service = sync_service or FamilyTreeSyncService()

    async def execute(
        self, dto: MarriageCreateDTO, *, tree_id: UUID
    ) -> MarriageCreateResponseDTO:
        async with self.uow:
            spouse_a = await self.uow.persons.get_in_tree_or_raise(
                person_id=dto.spouse_a_id, tree_id=tree_id
            )
            spouse_b = await self.uow.persons.get_in_tree_or_raise(
                person_id=dto.spouse_b_id, tree_id=tree_id
            )

            if spouse_a.tree_id != tree_id or spouse_b.tree_id != tree_id:
                raise MarriageTreeMismatchException()

            self.marriage_rules_service.validate_marriage(
                spouse_a=spouse_a,
                spouse_b=spouse_b,
                marriage_date=dto.married_at,
            )

            marriage = Marriage(
                id=None,
                tree_id=tree_id,
                spouse_a_id=dto.spouse_a_id,
                spouse_b_id=dto.spouse_b_id,
                married_at=dto.married_at,
            )

            try:
                marriage = await self.uow.marriages.create(marriage)
                await self.uow.commit()
            except IntegrityError:
                raise

            self.sync_service.upsert_spouse(marriage.spouse_a_id, marriage.spouse_b_id)

            return MarriageCreateMapper.to_response(marriage=marriage)
