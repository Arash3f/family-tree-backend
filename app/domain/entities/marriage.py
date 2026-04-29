from dataclasses import dataclass
from datetime import date

from app.domain.exceptions.marriage_exceptions import (
    DivorceBeforeMarriageException,
    MarriageAfterDivorceException,
    SelfMarriageException,
)


@dataclass
class Marriage:
    """
    Domain entity representing a marriage between two persons.

    This entity enforces business rules related to marriage lifecycle,
    including marriage creation, divorce handling, and date consistency.
    """

    id: int | None
    husband_id: int
    wife_id: int
    married_at: date
    divorced_at: date | None = None

    def __post_init__(self) -> None:
        self._validate_spouses()
        self._validate_dates()

    def is_active(self) -> bool:
        """Return True if the marriage is still active."""
        return self.divorced_at is None

    def divorce(self, divorced_at: date) -> None:
        """
        Mark the marriage as divorced.

        Args:
            divorced_at: Date when the divorce occurred.

        Raises:
            DivorceBeforeMarriageException:
                If the divorce date is before the marriage date.
        """
        if divorced_at < self.married_at:
            raise DivorceBeforeMarriageException()

        self.divorced_at = divorced_at

    def set_married_at(self, married_at: date) -> None:
        """
        Update the marriage date.

        Raises:
            MarriageAfterDivorceException:
                If the new marriage date is after an existing divorce date.
        """
        if self.divorced_at and married_at > self.divorced_at:
            raise MarriageAfterDivorceException()

        self.married_at = married_at

    @property
    def safe_id(self) -> int:
        """
        Return the entity ID ensuring it exists.

        Raises:
            RuntimeError: If the entity has not been persisted yet.
        """
        if self.id is None:
            raise RuntimeError("Entity has no id")
        return self.id

    @property
    def safe_divorced_at(self) -> date:
        """
        Return the divorce date ensuring it exists.

        Raises:
            RuntimeError: If the marriage is still active.
        """
        if self.divorced_at is None:
            raise RuntimeError("Marriage has no divorced_at")
        return self.divorced_at

    def _validate_spouses(self) -> None:
        """Ensure that a person cannot marry themselves."""
        if self.husband_id == self.wife_id:
            raise SelfMarriageException()

    def _validate_dates(self) -> None:
        """Validate chronological order of marriage and divorce."""
        if self.divorced_at and self.divorced_at < self.married_at:
            raise DivorceBeforeMarriageException()
