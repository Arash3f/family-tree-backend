from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.entities.family_tree import TreeMemberRole


class FamilyTreeCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class FamilyTreeUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class FamilyTreeResponse(BaseModel):
    id: UUID
    name: str
    owner_user_id: UUID


class TreeMemberAddRequest(BaseModel):
    user_id: UUID


class TreeMembershipResponse(BaseModel):
    id: UUID
    tree_id: UUID
    user_id: UUID
    role: TreeMemberRole
