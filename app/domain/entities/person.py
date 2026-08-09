from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from uuid import UUID

from app.domain.exceptions.common_exceptions import UnExpectedIdException
from app.domain.exceptions.person_exceptions import (
    InvalidBirthDateException,
    SameParentException,
    SelfParentException,
    TooManyBiologicalParentsException,
)


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class ParentRelationshipType(str, Enum):
    BIOLOGICAL = "biological"
    ADOPTIVE = "adoptive"
    STEP = "step"


@dataclass(frozen=True)
class ParentLink:
    parent_id: UUID
    relationship_type: ParentRelationshipType = ParentRelationshipType.BIOLOGICAL


@dataclass
class Person:
    """
    Represents a human being in the family tree domain.

    This entity encapsulates the core domain logic related to a person,
    including parental relationships and basic reasoning about family
    relationships.
    """

    id: UUID | None
    name: str
    gender: Gender
    birth_date: date | None = None
    death_date: date | None = None
    parents: list[ParentLink] = field(default_factory=list)
    marriage_id: UUID | None = None
    photo_object_key: str | None = None

    def __post_init__(self) -> None:
        """
        Validates domain invariants after initialization.

        Raises:
            InvalidBirthDateException:
                If the birth date is set in the future.

            SelfParentException:
                If a person is assigned as their own parent.

            SameParentException:
                If the same parent id appears more than once.

            TooManyBiologicalParentsException:
                If more than two biological parents are assigned.
        """

        if self.birth_date and self.birth_date > date.today():
            raise InvalidBirthDateException()

        if self.birth_date and self.death_date and self.death_date < self.birth_date:
            raise InvalidBirthDateException(
                detail=["death_date cannot be before birth_date"]
            )

        self._validate_parents(self.parents)

    def _validate_parents(self, parents: list[ParentLink]) -> None:
        parent_ids = [link.parent_id for link in parents]

        if self.id is not None and self.id in parent_ids:
            raise SelfParentException()

        if len(parent_ids) != len(set(parent_ids)):
            raise SameParentException()

        biological_count = sum(
            1
            for link in parents
            if link.relationship_type is ParentRelationshipType.BIOLOGICAL
        )
        if biological_count > 2:
            raise TooManyBiologicalParentsException()

    def set_parents(self, parents: list[ParentLink]) -> None:
        self._validate_parents(parents)
        self.parents = list(parents)

    def add_parent(self, parent: ParentLink) -> None:
        self.set_parents([*self.parents, parent])

    @property
    def parent_ids(self) -> list[UUID]:
        return [link.parent_id for link in self.parents]

    def age(self, on: date | None = None) -> int | None:
        """
        Calculates the age of the person.

        Args:
            on:
                The date on which to calculate the age.
                Defaults to today's date.

        Returns:
            The calculated age in years, or None if birth_date is not set.
        """

        if not self.birth_date:
            return None

        on = on or date.today()

        age = on.year - self.birth_date.year

        if (on.month, on.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1

        return age

    def is_parent_of(self, other: "Person") -> bool:
        """
        Determines whether this person is a parent of another person.
        """

        return self.id is not None and self.id in other.parent_ids

    def is_child_of(self, other: "Person") -> bool:
        """
        Determines whether this person is a child of another person.
        """

        return other.id is not None and other.id in self.parent_ids

    def is_sibling_of(self, other: "Person") -> bool:
        """
        Determines whether two persons share at least one parent.
        """

        if self.id == other.id:
            return False

        return bool(set(self.parent_ids) & set(other.parent_ids))

    @property
    def safe_id(self) -> UUID:
        """
        Returns the person's ID.

        In some parts of the project, a complete Person object may still show
        a type warning because the `id` field is optional. This property
        returning the actual ID value.

        Raises:
            UnExpectedPersonIdException:
                If the person's `id` is None.
        """

        if self.id is None:
            raise UnExpectedIdException(detail=[f"person's name is {self.name}"])
        return self.id
