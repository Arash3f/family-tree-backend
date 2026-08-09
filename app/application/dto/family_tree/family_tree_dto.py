from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.entities.family_tree import FamilyTree, TreeMemberRole, TreeMembership


class FamilyTreeCreateDTO(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class FamilyTreeUpdateDTO(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class FamilyTreeResponseDTO(BaseModel):
    id: UUID
    name: str
    owner_user_id: UUID


class TreeMemberAddDTO(BaseModel):
    user_id: UUID


class TreeMembershipResponseDTO(BaseModel):
    id: UUID
    tree_id: UUID
    user_id: UUID
    role: TreeMemberRole


class FamilyTreeMapper:
    @staticmethod
    def to_response(tree: FamilyTree) -> FamilyTreeResponseDTO:
        return FamilyTreeResponseDTO(
            id=tree.safe_id,
            name=tree.name,
            owner_user_id=tree.owner_user_id,
        )

    @staticmethod
    def membership_to_response(
        membership: TreeMembership,
    ) -> TreeMembershipResponseDTO:
        return TreeMembershipResponseDTO(
            id=membership.safe_id,
            tree_id=membership.tree_id,
            user_id=membership.user_id,
            role=membership.role,
        )
