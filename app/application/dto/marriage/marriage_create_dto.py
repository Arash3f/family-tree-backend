from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.marriage import Marriage


class MarriageCreateDTO(BaseModel):
    husband_id: UUID
    wife_id: UUID
    married_at: date


class MarriageCreateResponseDTO(BaseModel):
    id: UUID
    husband_id: UUID
    wife_id: UUID
    married_at: date
    divorced_at: date | None


class MarriageCreateMapper(BaseModel):
    @staticmethod
    def to_response(marriage: Marriage) -> MarriageCreateResponseDTO:
        return MarriageCreateResponseDTO(
            id=marriage.safe_id,
            husband_id=marriage.husband_id,
            wife_id=marriage.wife_id,
            married_at=marriage.married_at,
            divorced_at=marriage.divorced_at,
        )
