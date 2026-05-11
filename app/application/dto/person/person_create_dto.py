from datetime import date

from pydantic import BaseModel

from app.domain.entities.person import Gender, Person


class PersonCreateDTO(BaseModel):
    name: str
    gender: Gender
    birth_date: date | None
    father_id: int | None
    mother_id: int | None


class PersonCreateResponseDTO(BaseModel):
    id: int
    name: str
    gender: Gender
    birth_date: date | None
    father_id: int | None
    mother_id: int | None


class PersonCreateMapper(BaseModel):
    @staticmethod
    def to_response(person: Person) -> PersonCreateResponseDTO:
        return PersonCreateResponseDTO(
            id=person.safe_id,
            name=person.name,
            gender=person.gender,
            birth_date=person.birth_date,
            father_id=person.father_id,
            mother_id=person.mother_id,
        )
