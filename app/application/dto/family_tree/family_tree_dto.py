from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.domain.entities.family_tree import FamilyTree, TreeMemberRole, TreeMembership
from app.domain.shared.tree_access import TreeAccessPermissions


class FamilyTreeCreateDTO(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class FamilyTreeUpdateDTO(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class FamilyTreeResponseDTO(BaseModel):
    id: UUID
    name: str
    owner_user_id: UUID
    my_permissions: list[str] = Field(default_factory=list)


class TreeMemberAddDTO(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    permissions: list[str] = Field(default_factory=lambda: [TreeAccessPermissions.VIEW])

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, value: list[str]) -> list[str]:
        unknown = [name for name in value if not TreeAccessPermissions.is_known(name)]
        if unknown:
            raise ValueError(f"Unknown tree access permissions: {unknown}")
        return TreeAccessPermissions.normalize(value)


class TreeMemberUpdateDTO(BaseModel):
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


class TreeMembershipResponseDTO(BaseModel):
    id: UUID
    tree_id: UUID
    user_id: UUID
    role: TreeMemberRole
    permissions: list[str] = Field(default_factory=list)
    username: str | None = None


class FamilyTreeMapper:
    @staticmethod
    def to_response(
        tree: FamilyTree, *, my_permissions: list[str] | None = None
    ) -> FamilyTreeResponseDTO:
        return FamilyTreeResponseDTO(
            id=tree.safe_id,
            name=tree.name,
            owner_user_id=tree.owner_user_id,
            my_permissions=list(my_permissions or []),
        )

    @staticmethod
    def membership_to_response(
        membership: TreeMembership,
        *,
        username: str | None = None,
    ) -> TreeMembershipResponseDTO:
        return TreeMembershipResponseDTO(
            id=membership.safe_id,
            tree_id=membership.tree_id,
            user_id=membership.user_id,
            role=membership.role,
            permissions=membership.effective_permissions(),
            username=username,
        )
