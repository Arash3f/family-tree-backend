from dataclasses import dataclass
from typing import List

from app.domain.exceptions.common import UnExpectedIdException


@dataclass
class Role:
    """
    Represents a user role's.

    This entity encapsulates the core domain logic related to role
    """

    name: str
    permission_ids: List[int]
    id: int | None = None

    def __post_init__(self) -> None:
        """
        Remove duplicate permissions after initialization
        """
        self.remove_duplicate_permission()

    def remove_duplicate_permission(self):
        """
        Remove duplicate permissions
        """
        self.permission_ids = list(dict.fromkeys(self.permission_ids))

    @property
    def safe_id(self) -> int:
        """
        Returns the role's ID.

        In some parts of the project, a complete Role object may still show
        a type warning because the `id` field is optional. This property
        returning the actual ID value.

        Raises:
            UnExpectedRoleIdException:
                If the role's `id` is None.
        """

        if self.id is None:
            raise UnExpectedIdException(detail=[f"role's name is {self.name}"])
        return self.id
