from dataclasses import dataclass
from uuid import UUID

from app.domain.exceptions.common_exceptions import UnExpectedIdException
from app.domain.services.password_hasher import PasswordHasher


@dataclass
class User:
    """
    Represents a user model.

    This entity encapsulates the core domain logic related to a user.
    """

    username: str
    password_hash: str
    id: UUID | None = None
    role_id: UUID | None = None

    def verify_password(self, plain_password: str, hasher: PasswordHasher) -> bool:
        """
        Verify whether the provided password matches the stored password hash.

        Args:
            plain_password (str): The plain text password provided by the user.
            hasher (PasswordHasher): Password hashing service used to perform verification.

        Returns:
            bool: True if the password matches the stored hash, otherwise False.
        """
        return hasher.verify(plain_password, self.password_hash)

    @property
    def safe_id(self) -> UUID:
        """
        Returns the user's ID.

        In some parts of the project, a complete Role object may still show
        a type warning because the `id` field is optional. This property
        returning the actual ID value.

        Raises:
            UnExpectedRoleIdException:
                If the user's `id` is None.
        """

        if self.id is None:
            raise UnExpectedIdException(detail=[f"user's username is {self.username}"])
        return self.id
