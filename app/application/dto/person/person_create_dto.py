from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.entities.person import (
    Gender,
    ParentLink,
    ParentRelationshipType,
    Person,
)


class ParentLinkDTO(BaseModel):
    parent_id: UUID
    relationship_type: ParentRelationshipType = ParentRelationshipType.BIOLOGICAL


class PersonCreateDTO(BaseModel):
    name: str
    gender: Gender
    birth_date: date | None
    death_date: date | None = None
    family_name: str | None = None
    birth_place: str | None = None
    death_place: str | None = None
    notes: str | None = None
    parents: list[ParentLinkDTO] = Field(default_factory=list)
    marriage_id: UUID | None = None
    photo_object_key: str | None = None


class PersonCreateResponseDTO(BaseModel):
    id: UUID
    name: str
    gender: Gender
    birth_date: date | None
    death_date: date | None = None
    family_name: str | None = None
    birth_place: str | None = None
    death_place: str | None = None
    notes: str | None = None
    parents: list[ParentLinkDTO] = Field(default_factory=list)
    marriage_id: UUID | None = None
    photo_object_key: str | None = None
    photo_url: str | None = None


class PersonCreateMapper(BaseModel):
    @staticmethod
    def to_response(
        person: Person, photo_url: str | None = None
    ) -> PersonCreateResponseDTO:
        return PersonCreateResponseDTO(
            id=person.safe_id,
            name=person.name,
            gender=person.gender,
            birth_date=person.birth_date,
            death_date=person.death_date,
            family_name=person.family_name,
            birth_place=person.birth_place,
            death_place=person.death_place,
            notes=person.notes,
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

    @staticmethod
    def to_domain_parents(parents: list[ParentLinkDTO]) -> list[ParentLink]:
        return [
            ParentLink(
                parent_id=link.parent_id,
                relationship_type=link.relationship_type,
            )
            for link in parents
        ]
