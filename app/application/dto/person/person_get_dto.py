from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.application.dto.person.person_create_dto import ParentLinkDTO
from app.domain.entities.person import Gender, Person


class PersonGetResponseDTO(BaseModel):
    id: UUID
    name: str
    gender: Gender
    birth_date: date | None
    death_date: date | None = None
    parents: list[ParentLinkDTO] = Field(default_factory=list)
    marriage_id: UUID | None = None
    photo_object_key: str | None = None
    photo_url: str | None = None


class PersonGetMapper(BaseModel):
    @staticmethod
    def to_response(
        person: Person, photo_url: str | None = None
    ) -> PersonGetResponseDTO:
        return PersonGetResponseDTO(
            id=person.safe_id,
            name=person.name,
            gender=person.gender,
            birth_date=person.birth_date,
            death_date=person.death_date,
            parents=[
                ParentLinkDTO(
                    parent_id=link.parent_id,
                    relationship_type=link.relationship_type,
                )
                for link in person.parents
            ],
            marriage_id=person.marriage_id,
            photo_object_key=person.photo_object_key,
            photo_url=photo_url,
        )
