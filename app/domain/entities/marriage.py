from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.domain.exceptions.common_exceptions import UnExpectedIdException
from app.domain.exceptions.marriage_exceptions import (
    DivorceBeforeMarriageException,
    MarriageAfterDivorceException,
    MarriageAlreadyDivorcedException,
    SelfMarriageException,
)


@dataclass
class Marriage:
    """
    Domain entity representing a marriage between two persons.

    This entity enforces business rules related to marriage lifecycle,
    including marriage creation, divorce handling, and date consistency.
    """

    id: UUID | None
    tree_id: UUID
    spouse_a_id: UUID
    spouse_b_id: UUID
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

        This is the one-off business action. Correcting the date of a divorce
        that already happened goes through `set_divorced_at`.

        Args:
            divorced_at: Date when the divorce occurred.

        Raises:
            MarriageAlreadyDivorcedException:
                If the marriage has already been divorced.
            DivorceBeforeMarriageException:
                If the divorce date is before the marriage date.
        """
        if self.divorced_at is not None:
            raise MarriageAlreadyDivorcedException(
                detail=[f"marriage was already divorced on {self.divorced_at}"]
            )

        self.set_divorced_at(divorced_at)

    def set_divorced_at(self, divorced_at: date) -> None:
        """
        Set or correct the divorce date.

        Raises:
            DivorceBeforeMarriageException:
                If the divorce date is before the marriage date.
        """
        if divorced_at < self.married_at:
            raise DivorceBeforeMarriageException()

        self.divorced_at = divorced_at

    def clear_divorce(self) -> None:
        """Reactivate the marriage by dropping its divorce date."""
        self.divorced_at = None

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
    def safe_id(self) -> UUID:
        """
        Return the entity ID ensuring it exists.

        Raises:
            UnExpectedIdException: If the entity has not been persisted yet.
        """
        if self.id is None:
            raise UnExpectedIdException(detail=["marriage has no id"])
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
        if self.spouse_a_id == self.spouse_b_id:
            raise SelfMarriageException()

    def _validate_dates(self) -> None:
        """Validate chronological order of marriage and divorce."""
        if self.divorced_at and self.divorced_at < self.married_at:
            raise DivorceBeforeMarriageException()
