from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.marriage import Marriage


class MarriageGetResponseDTO(BaseModel):
    id: UUID
    husband_id: UUID
    wife_id: UUID
    married_at: date
    divorced_at: date | None


class MarriageGetMapper(BaseModel):
    @staticmethod
    def to_response(marriage: Marriage) -> MarriageGetResponseDTO:
        return MarriageGetResponseDTO(
            id=marriage.safe_id,
            husband_id=marriage.husband_id,
            wife_id=marriage.wife_id,
            married_at=marriage.married_at,
            divorced_at=marriage.divorced_at,
        )
