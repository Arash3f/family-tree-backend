from app.application.dto.marriage.marriage_update_dto import (
    MarriageUpdateDTO,
    MarriageUpdateDTOMapper,
    MarriageUpdateField,
    MarriageUpdateResponseDTO,
)
from app.application.unit_of_work import UnitOfWork
from app.domain.services.marriage_rules import MarriageRulesService


class UpdateMarriageUseCase:
    def __init__(self, uow: UnitOfWork, marriage_rules_service: MarriageRulesService):
        self.uow = uow
        self.marriage_rules_service = marriage_rules_service

    async def execute(self, dto: MarriageUpdateDTO) -> MarriageUpdateResponseDTO:
        async with self.uow:
            update_data = dto.data.model_dump(exclude_unset=True)

            marriage = await self.uow.marriages.get_or_raise(
                marriage_id=dto.where.marriage_id
            )

            update_data_enum = {
                MarriageUpdateField(key): value for key, value in update_data.items()
            }

            husband_id = update_data_enum.pop(MarriageUpdateField.HUSBAND_ID, None)
            wife_id = update_data_enum.pop(MarriageUpdateField.WIFE_ID, None)

            needs_validation = False

            if husband_id is not None:
                husband = await self.uow.persons.get_or_raise(husband_id)
                marriage.husband_id = husband.safe_id
                needs_validation = True
            else:
                husband = None

            if wife_id is not None:
                wife = await self.uow.persons.get_or_raise(wife_id)
                marriage.wife_id = wife.safe_id
                needs_validation = True
            else:
                wife = None

            if MarriageUpdateField.MARRIAGE_AT in update_data_enum:
                marriage.set_married_at = update_data_enum[
                    MarriageUpdateField.MARRIAGE_AT
                ]
                needs_validation = True

            if MarriageUpdateField.DIVORCE_AT in update_data_enum:
                marriage.divorced_at = update_data_enum[MarriageUpdateField.DIVORCE_AT]

            if needs_validation:
                if husband is None:
                    husband = await self.uow.persons.get_or_raise(marriage.husband_id)

                if wife is None:
                    wife = await self.uow.persons.get_or_raise(marriage.wife_id)

                self.marriage_rules_service.validate_marriage(
                    husband=husband, wife=wife, marriage_date=marriage.married_at
                )

            for field, value in update_data_enum.items():
                setattr(marriage, field.value, value)

            marriage = await self.uow.marriages.update(marriage=marriage)

            await self.uow.commit()

            return MarriageUpdateDTOMapper.to_response(marriage=marriage)
