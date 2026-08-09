from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.marriage import Marriage


class MarriageCreateDTO(BaseModel):
    spouse_a_id: UUID
    spouse_b_id: UUID
    married_at: date


class MarriageCreateResponseDTO(BaseModel):
    id: UUID
    spouse_a_id: UUID
    spouse_b_id: UUID
    married_at: date
    divorced_at: date | None


class MarriageCreateMapper(BaseModel):
    @staticmethod
    def to_response(marriage: Marriage) -> MarriageCreateResponseDTO:
        return MarriageCreateResponseDTO(
            id=marriage.safe_id,
            spouse_a_id=marriage.spouse_a_id,
            spouse_b_id=marriage.spouse_b_id,
            married_at=marriage.married_at,
            divorced_at=marriage.divorced_at,
        )
