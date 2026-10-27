from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from app.domain.exceptions.common_exceptions import UnExpectedIdException
from app.domain.services.password_hasher import PasswordHasher
from app.domain.shared.account_type import AccountType, effective_account_type
from app.domain.shared.user_preferences import PreferredLocale, PreferredTheme


@dataclass
class User:
    """
    Represents a user model.

    This entity encapsulates the core domain logic related to a user.
    """

    username: str
    password_hash: str
    fullname: str = ""
    email: str | None = None
    phone: str | None = None
    id: UUID | None = None
    role_id: UUID | None = None
    account_type: AccountType = AccountType.FREE
    # Last day (UTC) a paid plan covers; None means it never lapses.
    paid_until: date | None = None
    is_active: bool = True
    preferred_locale: PreferredLocale | None = None
    preferred_theme: PreferredTheme | None = None
    # Populated only on list queries (max session created_at); not persisted on User.
    last_session_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.fullname:
            self.fullname = self.username
        if isinstance(self.account_type, str):
            self.account_type = AccountType(self.account_type)
        if isinstance(self.preferred_locale, str):
            self.preferred_locale = PreferredLocale(self.preferred_locale)
        if isinstance(self.preferred_theme, str):
            self.preferred_theme = PreferredTheme(self.preferred_theme)

    @property
    def is_free(self) -> bool:
        """
        Whether free-account quotas apply right now.

        A paid account whose `paid_until` day is behind us counts as free at
        once, before the daily expiry task gets to store it as such.
        """
        return self.effective_account_type is AccountType.FREE

    @property
    def effective_account_type(self) -> AccountType:
        """The plan in force today: the stored one, unless a paid plan lapsed."""
        return effective_account_type(self.account_type, self.paid_until)

    def verify_password(self, plain_password: str, hasher: PasswordHasher) -> bool:
        """
        Verify whether the provided password matches the stored password hash.

        Args:
            plain_password (str): The plain text password provided by the user.
            hasher (PasswordHasher): Password hashing service used to perform
                verification.

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
