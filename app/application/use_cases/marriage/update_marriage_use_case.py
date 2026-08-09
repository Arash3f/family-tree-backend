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

            old_spouse_a_id = marriage.spouse_a_id
            old_spouse_b_id = marriage.spouse_b_id
            old_divorced_at = marriage.divorced_at

            update_data_enum = {
                MarriageUpdateField(key): value for key, value in update_data.items()
            }

            spouse_a_id = update_data_enum.pop(MarriageUpdateField.spouse_a_id, None)
            spouse_b_id = update_data_enum.pop(MarriageUpdateField.spouse_b_id, None)

            needs_validation = False
            spouse_a = None
            spouse_b = None

            if spouse_a_id is not None:
                spouse_a = await self.uow.persons.get_or_raise(person_id=spouse_a_id)
                marriage.spouse_a_id = spouse_a.safe_id
                needs_validation = True

            if spouse_b_id is not None:
                spouse_b = await self.uow.persons.get_or_raise(person_id=spouse_b_id)
                marriage.spouse_b_id = spouse_b.safe_id
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
                if spouse_a is None:
                    spouse_a = await self.uow.persons.get_or_raise(
                        person_id=marriage.spouse_a_id
                    )

                if spouse_b is None:
                    spouse_b = await self.uow.persons.get_or_raise(
                        person_id=marriage.spouse_b_id
                    )

                self.marriage_rules_service.validate_marriage(
                    spouse_a=spouse_a,
                    spouse_b=spouse_b,
                    marriage_date=marriage.married_at,
                )

            for field, value in update_data_enum.items():
                setattr(marriage, field.value, value)

            try:
                marriage = await self.uow.marriages.update(marriage=marriage)
                await self.uow.commit()
            except IntegrityError:
                raise

            spouses_changed = (
                old_spouse_a_id != marriage.spouse_a_id
                or old_spouse_b_id != marriage.spouse_b_id
            )
            became_divorced = (
                old_divorced_at is None and marriage.divorced_at is not None
            )
            became_active = old_divorced_at is not None and marriage.divorced_at is None
            is_active = marriage.divorced_at is None

            if became_divorced:
                self.sync_service.remove_spouse(old_spouse_a_id, old_spouse_b_id)
            elif is_active and spouses_changed:
                self.sync_service.replace_spouse(
                    old_person_id_1=old_spouse_a_id,
                    old_person_id_2=old_spouse_b_id,
                    new_person_id_1=marriage.spouse_a_id,
                    new_person_id_2=marriage.spouse_b_id,
                )
            elif became_active:
                self.sync_service.upsert_spouse(
                    marriage.spouse_a_id, marriage.spouse_b_id
                )

            return MarriageUpdateDTOMapper.to_response(marriage=marriage)
