from passlib.context import CryptContext

from app.domain.services.password_hasher import PasswordHasher

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class Argon2PasswordHasher(PasswordHasher):
    """
    Argon2-based implementation of the PasswordHasher interface.

    This class provides a concrete implementation of the PasswordHasher
    domain service using the Argon2 password hashing algorithm via
    Passlib's CryptContext.

    Argon2 is a memory-hard, CPU-intensive algorithm designed to resist
    brute-force and GPU-based attacks, making it suitable for
    production-grade password storage.

    This implementation belongs to the infrastructure layer and must
    not be referenced directly by the domain layer.
    """

    def hash(self, password: str) -> str:
        """
        Hash a plain text password using the Argon2 algorithm.

        Args:
            password (str): The raw password provided by the user.

        Returns:
            str: A securely generated Argon2 hash suitable for persistent storage.
        """
        return pwd_context.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify whether a plain text password matches a stored Argon2 hash.

        Args:
            plain_password (str): The raw password provided for authentication.
            hashed_password (str): The stored Argon2 password hash.

        Returns:
            bool: True if the password matches the hash, otherwise False.
        """
        return pwd_context.verify(plain_password, hashed_password)
