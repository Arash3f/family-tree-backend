from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    """
    Abstract interface for password hashing and verification.

    This service defines the contract for hashing plain text passwords
    and verifying them against stored password hashes. Implementations
    should apply secure password hashing algorithms such as Argon2 or
    bcrypt.

    This interface belongs to the domain layer and must remain
    independent from specific cryptographic libraries. Concrete
    implementations are expected to reside in the infrastructure layer.
    """

    @abstractmethod
    def hash(self, password: str) -> str:
        """
        Hash a plain text password.

        Args:
            password (str): The raw password provided by the user.

        Returns:
            str: A securely generated password hash suitable for storage.
        """
        pass

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify whether a plain text password matches a stored hash.

        Args:
            plain_password (str): The raw password provided for authentication.
            hashed_password (str): The stored password hash to compare against.

        Returns:
            bool: True if the password matches the stored hash, otherwise False.
        """
        pass
