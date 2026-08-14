from uuid import UUID

import strawberry

from app.domain.entities.family_tree import TreeMemberRole
from app.domain.shared.tree_access import TreeAccessPermissions


@strawberry.type
class FamilyTreeType:
    id: UUID
    name: str
    owner_user_id: UUID
    my_permissions: list[str]


@strawberry.type
class TreeMembershipType:
    id: UUID
    tree_id: UUID
    user_id: UUID
    role: TreeMemberRole
    permissions: list[str]
    username: str | None = None


@strawberry.input
class FamilyTreeCreateInput:
    name: str


@strawberry.input
class FamilyTreeUpdateInput:
    name: str


@strawberry.input
class TreeMemberAddInput:
    username: str
    permissions: list[str] | None = None


@strawberry.input
class TreeMemberUpdateInput:
    permissions: list[str]


def family_tree_from_mapping(data: dict) -> FamilyTreeType:
    return FamilyTreeType(
        id=data["id"],
        name=data["name"],
        owner_user_id=data["owner_user_id"],
        my_permissions=list(data.get("my_permissions") or []),
    )


def tree_membership_from_mapping(data: dict) -> TreeMembershipType:
    return TreeMembershipType(
        id=data["id"],
        tree_id=data["tree_id"],
        user_id=data["user_id"],
        role=data["role"],
        permissions=list(data.get("permissions") or [TreeAccessPermissions.VIEW]),
        username=data.get("username"),
    )
