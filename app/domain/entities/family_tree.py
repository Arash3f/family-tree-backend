from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID

from app.domain.exceptions.common_exceptions import UnExpectedIdException
from app.domain.shared.tree_access import TreeAccessPermissions


class TreeMemberRole(str, Enum):
    OWNER = "owner"
    MEMBER = "member"


@dataclass
class FamilyTree:
    id: UUID | None
    name: str
    owner_user_id: UUID

    @property
    def safe_id(self) -> UUID:
        if self.id is None:
            raise UnExpectedIdException(detail=[f"family tree name is {self.name}"])
        return self.id


@dataclass
class TreeMembership:
    id: UUID | None
    tree_id: UUID
    user_id: UUID
    role: TreeMemberRole
    permissions: list[str] = field(default_factory=lambda: [TreeAccessPermissions.VIEW])

    @property
    def safe_id(self) -> UUID:
        if self.id is None:
            raise UnExpectedIdException(
                detail=[f"membership tree_id={self.tree_id} user_id={self.user_id}"]
            )
        return self.id

    def is_owner(self) -> bool:
        return self.role is TreeMemberRole.OWNER

    def effective_permissions(self) -> list[str]:
        if self.is_owner():
            return sorted(TreeAccessPermissions.ALL)
        return TreeAccessPermissions.normalize(self.permissions)

    def has_access(self, permission_name: str) -> bool:
        return permission_name in self.effective_permissions()
