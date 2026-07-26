from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.person import Gender, Person


class PersonGetResponseDTO(BaseModel):
    id: UUID
    name: str
    gender: Gender
    birth_date: date | None
    death_date: date | None = None
    father_id: UUID | None
    mother_id: UUID | None


class PersonGetMapper(BaseModel):
    @staticmethod
    def to_response(person: Person) -> PersonGetResponseDTO:
        return PersonGetResponseDTO(
            id=person.safe_id,
            name=person.name,
            gender=person.gender,
            birth_date=person.birth_date,
            death_date=person.death_date,
            father_id=person.father_id,
            mother_id=person.mother_id,
        )
