from datetime import date
from enum import Enum

from pydantic import BaseModel

from app.domain.entities.person import Gender, Person


class PersonUpdateField(str, Enum):
    MOTHER_ID = "mother_id"
    FATHER_ID = "father_id"
    NAME = "name"
    GENDER = "gender"
    BIRTH_DATE = "birth_date"


class _PersonUpdateDataDTO(BaseModel):
    name: str | None
    gender: Gender | None
    birth_date: date | None
    father_id: int | None
    mother_id: int | None


class _PersonUpdateWhereDTO(BaseModel):
    person_id: int


class PersonUpdateDTO(BaseModel):
    data: _PersonUpdateDataDTO
    where: _PersonUpdateWhereDTO


class PersonUpdateResponseDTO(BaseModel):
    id: int
    name: str
    gender: Gender
    birth_date: date | None
    father_id: int | None
    mother_id: int | None


class PersonUpdateMapper(BaseModel):
    @staticmethod
    def to_response(person: Person) -> PersonUpdateResponseDTO:
        return PersonUpdateResponseDTO(
            id=person.safe_id,
            name=person.name,
            gender=person.gender,
            birth_date=person.birth_date,
            father_id=person.father_id,
            mother_id=person.mother_id,
        )
