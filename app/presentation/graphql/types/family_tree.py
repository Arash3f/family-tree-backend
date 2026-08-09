from uuid import UUID

import strawberry

from app.domain.entities.family_tree import TreeMemberRole


@strawberry.type
class FamilyTreeType:
    id: UUID
    name: str
    owner_user_id: UUID


@strawberry.type
class TreeMembershipType:
    id: UUID
    tree_id: UUID
    user_id: UUID
    role: TreeMemberRole


@strawberry.input
class FamilyTreeCreateInput:
    name: str


@strawberry.input
class FamilyTreeUpdateInput:
    name: str


@strawberry.input
class TreeMemberAddInput:
    user_id: UUID


def family_tree_from_mapping(data: dict) -> FamilyTreeType:
    return FamilyTreeType(
        id=data["id"],
        name=data["name"],
        owner_user_id=data["owner_user_id"],
    )


def tree_membership_from_mapping(data: dict) -> TreeMembershipType:
    return TreeMembershipType(
        id=data["id"],
        tree_id=data["tree_id"],
        user_id=data["user_id"],
        role=data["role"],
    )
