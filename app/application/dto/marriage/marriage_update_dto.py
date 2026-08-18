from datetime import date
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.marriage import Marriage


class MarriageUpdateField(StrEnum):
    spouse_a_id = "spouse_a_id"
    spouse_b_id = "spouse_b_id"
    MARRIAGE_AT = "married_at"
    DIVORCE_AT = "divorced_at"


class _MarriageUpdateDataDTO(BaseModel):
    spouse_a_id: UUID | None = None
    spouse_b_id: UUID | None = None
    married_at: date | None = None
    divorced_at: date | None = None


class _MarriageUpdateWhereDTO(BaseModel):
    marriage_id: UUID


class MarriageUpdateDTO(BaseModel):
    data: _MarriageUpdateDataDTO
    where: _MarriageUpdateWhereDTO


class MarriageUpdateResponseDTO(BaseModel):
    id: UUID
    spouse_a_id: UUID
    spouse_b_id: UUID
    married_at: date
    divorced_at: date | None


class MarriageUpdateDTOMapper(BaseModel):
    @staticmethod
    def to_response(marriage: Marriage) -> MarriageUpdateResponseDTO:
        return MarriageUpdateResponseDTO(
            id=marriage.safe_id,
            spouse_a_id=marriage.spouse_a_id,
            spouse_b_id=marriage.spouse_b_id,
            married_at=marriage.married_at,
            divorced_at=marriage.divorced_at,
        )
