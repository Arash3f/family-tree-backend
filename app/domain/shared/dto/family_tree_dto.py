from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

# ==========================================
# Base DTO
# ==========================================


class PersonBaseDTO(BaseModel):
    full_name: str
    gender: str = Field(pattern="^(MALE|FEMALE)$")
    birth_date: date | None = None
    death_date: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PersonCompleteBaseDTO(PersonBaseDTO):
    id: UUID


# ==========================================
# Person DTOs
# ==========================================


class PersonUpsertDTO(PersonBaseDTO):
    id: UUID
    tree_id: UUID


class PersonResponseDTO(PersonBaseDTO):
    id: UUID
    tree_id: UUID | None = None


class PersonIdDTO(BaseModel):
    id: UUID
    tree_id: UUID | None = None


# ==========================================
# Relationship DTOs
# ==========================================


class ParentRelationshipDTO(BaseModel):
    parent_id: UUID
    child_id: UUID


class SpouseRelationshipDTO(BaseModel):
    person_id_1: UUID
    person_id_2: UUID


class DeleteRelationshipDTO(BaseModel):
    parent_id: UUID
    child_id: UUID


class DeleteSpouseRelationshipDTO(BaseModel):
    person_id_1: UUID
    person_id_2: UUID


class ParentRelationshipResponseDTO(BaseModel):
    parent: PersonCompleteBaseDTO
    child: PersonCompleteBaseDTO


class SpouseRelationshipResponseDTO(BaseModel):
    person_1: PersonCompleteBaseDTO
    person_2: PersonCompleteBaseDTO


class RelationshipPathDTO(BaseModel):
    from_person_id: UUID
    to_person_id: UUID
    found: bool
    distance: int | None = None
    path_person_ids: list[UUID] = Field(default_factory=list)
    relationship_types: list[str] = Field(default_factory=list)
