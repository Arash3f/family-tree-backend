from dataclasses import dataclass
from datetime import date
from enum import Enum

from app.domain.exceptions.common_exceptions import UnExpectedIdException
from app.domain.exceptions.person_exceptions import (
    InvalidBirthDateException,
    SameParentException,
    SelfParentException,
)


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


@dataclass
class Person:
    """
    Represents a human being in the family tree domain.

    This entity encapsulates the core domain logic related to a person,
    including parental relationships and basic reasoning about family
    relationships.
    """

    id: int | None
    name: str
    gender: Gender
    birth_date: date | None = None
    father_id: int | None = None
    mother_id: int | None = None

    def __post_init__(self) -> None:
        """
        Validates domain invariants after initialization.

        Raises:
            InvalidBirthDateException:
                If the birth date is set in the future.

            SelfParentException:
                If a person is assigned as their own parent.
        """

        # Validate birth_date!
        if self.birth_date and self.birth_date > date.today():
            raise InvalidBirthDateException()

        # Validate self parent!
        if self.id is not None:
            if self.father_id == self.id or self.mother_id == self.id:
                raise SelfParentException()

        if (
            self.father_id is not None
            and self.mother_id is not None
            and self.father_id == self.mother_id
        ):
            raise SameParentException()

    def set_father(self, father_id: int) -> None:
        """
        Assigns a father to the person.

        Args:
            father_id:
                The ID of the father.

        Raises:
            SelfParentException:
                If the person is assigned as their own father.
        """

        if self.id is not None and father_id == self.id:
            raise SelfParentException()

        if self.mother_id is not None and self.mother_id == father_id:
            raise SameParentException()

        self.father_id = father_id

    def set_mother(self, mother_id: int) -> None:
        """
        Assigns a mother to the person.

        Args:
            mother_id:
                The ID of the mother.

        Raises:
            SelfParentException:
                If the person is assigned as their own mother.
        """

        if self.id is not None and mother_id == self.id:
            raise SelfParentException()

        if self.father_id is not None and self.father_id == mother_id:
            raise SameParentException()

        self.mother_id = mother_id

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

        Args:
            other:
                The target person

        Returns:
            The calculated age in years, or None if birth_date is not set.
        """

        return other.father_id == self.id or other.mother_id == self.id

    def is_child_of(self, other: "Person") -> bool:
        """
        Determines whether this person is a child of another person.

        Args:
            other:
                The target person

        Returns:
            The calculated age in years, or None if birth_date is not set.
        """
        return self.father_id == other.id or self.mother_id == other.id

    def is_sibling_of(self, other: "Person") -> bool:
        """
        Determines whether two persons share at least one parent.

        Args:
            other:
                The target person
        """

        if self.id == other.id:
            return False

        same_father = self.father_id is not None and self.father_id == other.father_id

        same_mother = self.mother_id is not None and self.mother_id == other.mother_id

        return same_father or same_mother

    @property
    def safe_id(self) -> int:
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
