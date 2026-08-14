from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.domain.entities.family_tree import TreeMemberRole
from app.domain.shared.tree_access import TreeAccessPermissions


class FamilyTreeCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class FamilyTreeUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class FamilyTreeResponse(BaseModel):
    id: UUID
    name: str
    owner_user_id: UUID
    my_permissions: list[str] = Field(default_factory=list)


class TreeMemberAddRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    permissions: list[str] = Field(default_factory=lambda: [TreeAccessPermissions.VIEW])

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, value: list[str]) -> list[str]:
        unknown = [name for name in value if not TreeAccessPermissions.is_known(name)]
        if unknown:
            raise ValueError(f"Unknown tree access permissions: {unknown}")
        return TreeAccessPermissions.normalize(value)


class TreeMemberUpdateRequest(BaseModel):
    permissions: list[str]

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("At least one tree access permission is required")
        unknown = [name for name in value if not TreeAccessPermissions.is_known(name)]
        if unknown:
            raise ValueError(f"Unknown tree access permissions: {unknown}")
        return TreeAccessPermissions.normalize(value)


class TreeMembershipResponse(BaseModel):
    id: UUID
    tree_id: UUID
    user_id: UUID
    role: TreeMemberRole
    permissions: list[str] = Field(default_factory=list)
    username: str | None = None
