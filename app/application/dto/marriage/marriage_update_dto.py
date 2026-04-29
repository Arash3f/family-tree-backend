from datetime import date
from enum import Enum

from pydantic import BaseModel

from app.domain.entities.marriage import Marriage


class MarriageUpdateField(str, Enum):
    HUSBAND_ID = "husband_id"
    WIFE_ID = "wife_id"
    MARRIAGE_AT = "married_at"
    DIVORCE_AT = "divorced_at"


class _MarriageUpdateDataDTO(BaseModel):
    husband_id: int | None
    wife_id: int | None
    married_at: date | None
    divorced_at: date | None


class _MarriageUpdateWhereDTO(BaseModel):
    marriage_id: int


class MarriageUpdateDTO(BaseModel):
    data: _MarriageUpdateDataDTO
    where: _MarriageUpdateWhereDTO


class MarriageUpdateResponseDTO(BaseModel):
    id: int
    husband_id: int
    wife_id: int
    married_at: date
    divorced_at: date | None


class MarriageUpdateDTOMapper(BaseModel):
    @staticmethod
    def to_response(marriage: Marriage) -> MarriageUpdateResponseDTO:
        assert marriage.id is not None

        return MarriageUpdateResponseDTO(
            id=marriage.id,
            husband_id=marriage.husband_id,
            wife_id=marriage.wife_id,
            married_at=marriage.married_at,
            divorced_at=marriage.divorced_at,
        )
