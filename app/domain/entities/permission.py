from dataclasses import dataclass
from uuid import UUID

from app.domain.exceptions.common_exceptions import UnExpectedIdException


@dataclass
class Permission:
    """
    Represents a user permossions.

    This entity encapsulates the core domain logic related to a permossion.
    """

    name: str
    id: UUID | None = None

    @property
    def safe_id(self) -> UUID:
        """
        Returns the permission's ID.

        In some parts of the project, a complete Person object may still show
        a type warning because the `id` field is optional. This property
        returning the actual ID value.

        Raises:
            UnExpectedPersonIdException:
                If the permission's `id` is None.
        """

        if self.id is None:
            raise UnExpectedIdException(detail=[f"permission's name is {self.name}"])
        return self.id
