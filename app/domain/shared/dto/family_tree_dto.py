from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

# ==========================================
# Base DTO
# ==========================================


class PersonBaseDTO(BaseModel):
    full_name: str
    gender: str = Field(pattern="^(MALE|FEMALE)$")
    birth_date: Optional[date] = None
    death_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PersonCompleteBaseDTO(PersonBaseDTO):
    id: int


# ==========================================
# Person DTOs
# ==========================================


class PersonUpsertDTO(PersonBaseDTO):
    id: int


class PersonResponseDTO(PersonBaseDTO):
    id: int


class PersonIdDTO(BaseModel):
    id: int


# ==========================================
# Relationship DTOs
# ==========================================


class ParentRelationshipDTO(BaseModel):
    parent_id: int
    child_id: int


class SpouseRelationshipDTO(BaseModel):
    person_id_1: int
    person_id_2: int


class DeleteRelationshipDTO(BaseModel):
    parent_id: int
    child_id: int


class DeleteSpouseRelationshipDTO(BaseModel):
    person_id_1: int
    person_id_2: int


class ParentRelationshipResponseDTO(BaseModel):
    parent: PersonCompleteBaseDTO
    child: PersonCompleteBaseDTO


class SpouseRelationshipResponseDTO(BaseModel):
    person_1: PersonCompleteBaseDTO
    person_2: PersonCompleteBaseDTO
