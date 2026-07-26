from datetime import date
from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.marriage import Marriage


class MarriageUpdateField(str, Enum):
    HUSBAND_ID = "husband_id"
    WIFE_ID = "wife_id"
    MARRIAGE_AT = "married_at"
    DIVORCE_AT = "divorced_at"


class _MarriageUpdateDataDTO(BaseModel):
    husband_id: UUID | None = None
    wife_id: UUID | None = None
    married_at: date | None = None
    divorced_at: date | None = None


class _MarriageUpdateWhereDTO(BaseModel):
    marriage_id: UUID


class MarriageUpdateDTO(BaseModel):
    data: _MarriageUpdateDataDTO
    where: _MarriageUpdateWhereDTO


class MarriageUpdateResponseDTO(BaseModel):
    id: UUID
    husband_id: UUID
    wife_id: UUID
    married_at: date
    divorced_at: date | None


class MarriageUpdateDTOMapper(BaseModel):
    @staticmethod
    def to_response(marriage: Marriage) -> MarriageUpdateResponseDTO:
        return MarriageUpdateResponseDTO(
            id=marriage.safe_id,
            husband_id=marriage.husband_id,
            wife_id=marriage.wife_id,
            married_at=marriage.married_at,
            divorced_at=marriage.divorced_at,
        )
