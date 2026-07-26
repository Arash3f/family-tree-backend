from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.application.dto.marriage.marriage_update_dto import (
    MarriageUpdateDTO,
    MarriageUpdateDTOMapper,
    MarriageUpdateField,
    MarriageUpdateResponseDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.family_tree_sync_service import FamilyTreeSyncService
from app.domain.exceptions.marriage_exceptions import ActiveMarriageExistsException
from app.domain.services.marriage_rules import MarriageRulesService


class UpdateMarriageUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        marriage_rules_service: MarriageRulesService,
        sync_service: FamilyTreeSyncService | None = None,
    ):
        self.uow = uow
        self.marriage_rules_service = marriage_rules_service
        self.sync_service = sync_service or FamilyTreeSyncService()

    async def execute(self, dto: MarriageUpdateDTO) -> MarriageUpdateResponseDTO:
        async with self.uow:
            update_data = dto.data.model_dump(exclude_unset=True)

            marriage = await self.uow.marriages.get_or_raise(
                marriage_id=dto.where.marriage_id
            )

            old_husband_id = marriage.husband_id
            old_wife_id = marriage.wife_id
            old_divorced_at = marriage.divorced_at

            update_data_enum = {
                MarriageUpdateField(key): value for key, value in update_data.items()
            }

            husband_id = update_data_enum.pop(MarriageUpdateField.HUSBAND_ID, None)
            wife_id = update_data_enum.pop(MarriageUpdateField.WIFE_ID, None)

            needs_validation = False
            husband = None
            wife = None

            if husband_id is not None:
                husband = await self.uow.persons.get_or_raise(person_id=husband_id)
                marriage.husband_id = husband.safe_id
                needs_validation = True

            if wife_id is not None:
                wife = await self.uow.persons.get_or_raise(person_id=wife_id)
                marriage.wife_id = wife.safe_id
                needs_validation = True

            if MarriageUpdateField.MARRIAGE_AT in update_data_enum:
                marriage.set_married_at(
                    update_data_enum.pop(MarriageUpdateField.MARRIAGE_AT)
                )
                needs_validation = True

            if MarriageUpdateField.DIVORCE_AT in update_data_enum:
                divorced_at = update_data_enum.pop(MarriageUpdateField.DIVORCE_AT)
                if divorced_at is None:
                    marriage.divorced_at = None
                else:
                    marriage.divorce(divorced_at)

            if needs_validation:
                if husband is None:
                    husband = await self.uow.persons.get_or_raise(
                        person_id=marriage.husband_id
                    )

                if wife is None:
                    wife = await self.uow.persons.get_or_raise(
                        person_id=marriage.wife_id
                    )

                self.marriage_rules_service.validate_marriage(
                    husband=husband, wife=wife, marriage_date=marriage.married_at
                )

            for field, value in update_data_enum.items():
                setattr(marriage, field.value, value)

            if marriage.divorced_at is None:
                await self._ensure_no_overlapping_active(
                    husband_id=marriage.husband_id,
                    wife_id=marriage.wife_id,
                    exclude_marriage_id=marriage.safe_id,
                )

            try:
                marriage = await self.uow.marriages.update(marriage=marriage)
                await self.uow.commit()
            except IntegrityError as exc:
                await self._raise_if_active_marriage_conflict(exc)
                raise

            spouses_changed = (
                old_husband_id != marriage.husband_id
                or old_wife_id != marriage.wife_id
            )
            became_divorced = (
                old_divorced_at is None and marriage.divorced_at is not None
            )
            became_active = (
                old_divorced_at is not None and marriage.divorced_at is None
            )

            if became_divorced:
                self.sync_service.remove_spouse(old_husband_id, old_wife_id)
            elif spouses_changed:
                self.sync_service.replace_spouse(
                    old_person_id_1=old_husband_id,
                    old_person_id_2=old_wife_id,
                    new_person_id_1=marriage.husband_id,
                    new_person_id_2=marriage.wife_id,
                )
            elif became_active:
                self.sync_service.upsert_spouse(
                    marriage.husband_id, marriage.wife_id
                )

            return MarriageUpdateDTOMapper.to_response(marriage=marriage)

    async def _ensure_no_overlapping_active(
        self,
        husband_id: UUID,
        wife_id: UUID,
        exclude_marriage_id: UUID,
    ) -> None:
        if await self.uow.marriages.has_active_for_person(
            husband_id, exclude_marriage_id=exclude_marriage_id
        ):
            raise ActiveMarriageExistsException(
                detail=[f"Husband {husband_id} already has an active marriage"]
            )

        if await self.uow.marriages.has_active_for_person(
            wife_id, exclude_marriage_id=exclude_marriage_id
        ):
            raise ActiveMarriageExistsException(
                detail=[f"Wife {wife_id} already has an active marriage"]
            )

    @staticmethod
    async def _raise_if_active_marriage_conflict(exc: IntegrityError) -> None:
        message = str(getattr(exc, "orig", exc)).lower()
        if "uq_active_marriage" in message:
            raise ActiveMarriageExistsException() from exc
