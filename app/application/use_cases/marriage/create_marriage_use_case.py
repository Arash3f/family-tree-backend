from sqlalchemy.exc import IntegrityError

from app.application.dto.marriage.marriage_create_dto import (
    MarriageCreateDTO,
    MarriageCreateMapper,
    MarriageCreateResponseDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.family_tree_sync_service import FamilyTreeSyncService
from app.domain.entities.marriage import Marriage
from app.domain.exceptions.marriage_exceptions import ActiveMarriageExistsException
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

    async def execute(self, dto: MarriageCreateDTO) -> MarriageCreateResponseDTO:
        async with self.uow:
            husband = await self.uow.persons.get_or_raise(person_id=dto.husband_id)
            wife = await self.uow.persons.get_or_raise(person_id=dto.wife_id)

            self.marriage_rules_service.validate_marriage(
                husband=husband,
                wife=wife,
                marriage_date=dto.married_at,
            )

            if await self.uow.marriages.has_active_for_person(dto.husband_id):
                raise ActiveMarriageExistsException(
                    detail=[f"Husband {dto.husband_id} already has an active marriage"]
                )

            if await self.uow.marriages.has_active_for_person(dto.wife_id):
                raise ActiveMarriageExistsException(
                    detail=[f"Wife {dto.wife_id} already has an active marriage"]
                )

            marriage = Marriage(
                id=None,
                husband_id=dto.husband_id,
                wife_id=dto.wife_id,
                married_at=dto.married_at,
            )

            try:
                marriage = await self.uow.marriages.create(marriage)
                await self.uow.commit()
            except IntegrityError as exc:
                message = str(getattr(exc, "orig", exc)).lower()
                if "uq_active_marriage" in message:
                    raise ActiveMarriageExistsException() from exc
                raise

            self.sync_service.upsert_spouse(marriage.husband_id, marriage.wife_id)

            return MarriageCreateMapper.to_response(marriage=marriage)
