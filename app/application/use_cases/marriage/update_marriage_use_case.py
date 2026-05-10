from app.application.dto.marriage.marriage_update_dto import (
    MarriageUpdateDTO,
    MarriageUpdateDTOMapper,
    MarriageUpdateField,
    MarriageUpdateResponseDTO,
)
from app.application.services.unit_of_work import UnitOfWork
from app.domain.services.marriage_rules import MarriageRulesService


class UpdateMarriageUseCase:
    def __init__(self, uow: UnitOfWork, marriage_rules_service: MarriageRulesService):
        self.uow = uow
        self.marriage_rules_service = marriage_rules_service

    async def execute(self, dto: MarriageUpdateDTO) -> MarriageUpdateResponseDTO:
        async with self.uow:
            # ? Remove None fields
            update_data = dto.data.model_dump(exclude_unset=True)

            # ? find marriage
            marriage = await self.uow.marriages.get_or_raise(
                marriage_id=dto.where.marriage_id
            )

            # ? Convert update_data to new object and use enum for keys
            update_data_enum = {
                MarriageUpdateField(key): value for key, value in update_data.items()
            }

            # ? Read and pop husband_id and wife_id
            husband_id = update_data_enum.pop(MarriageUpdateField.HUSBAND_ID, None)
            wife_id = update_data_enum.pop(MarriageUpdateField.WIFE_ID, None)

            # ! If these field (husband or wife or married_at) change, marriage_rules_service should use
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
                marriage.set_married_at = update_data_enum[
                    MarriageUpdateField.MARRIAGE_AT
                ]
                needs_validation = True

            if MarriageUpdateField.DIVORCE_AT in update_data_enum:
                marriage.divorced_at = update_data_enum[MarriageUpdateField.DIVORCE_AT]

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

            # ? Update other fields automatically.
            for field, value in update_data_enum.items():
                setattr(marriage, field.value, value)

            marriage = await self.uow.marriages.update(marriage=marriage)

            await self.uow.commit()

            return MarriageUpdateDTOMapper.to_response(marriage=marriage)
