from datetime import date

from pydantic import BaseModel

from app.domain.entities.marriage import Marriage


class MarriageGetResponseDTO(BaseModel):
    id: int
    husband_id: int
    wife_id: int
    married_at: date
    divorced_at: date | None


class MarriageGetMapper(BaseModel):
    @staticmethod
    def to_response(marriage: Marriage) -> MarriageGetResponseDTO:
        assert marriage.id is not None

        return MarriageGetResponseDTO(
            id=marriage.id,
            husband_id=marriage.husband_id,
            wife_id=marriage.wife_id,
            married_at=marriage.married_at,
            divorced_at=marriage.divorced_at,
        )
