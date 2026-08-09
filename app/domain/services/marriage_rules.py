from datetime import date

from app.domain.entities.person import Person
from app.domain.exceptions.marriage_exceptions import (
    InvalidMarriageGenderException,
    SelfMarriageException,
    UnderageMarriageException,
)


class MarriageRulesService:
    """
    Service for validating marriage rules and business constraints.
    """

    MIN_MARRIAGE_AGE = 18

    @classmethod
    def validate_marriage(
        cls,
        spouse_a: Person,
        spouse_b: Person,
        marriage_date: date,
    ) -> None:
        """
        Validate marriage between two persons according to business rules.

        Checks:
            - Spouses must not be the same person (no self-marriage).
            - Spouses must be of opposite gender.
            - Both parties must be at least the minimum legal marriage age.

        Raises:
            SelfMarriageException:
                If both spouses are the same person.
            InvalidMarriageGenderException:
                If both spouses have the same gender.
            UnderageMarriageException:
                If either party is under the minimum marriage age.
        """
        if spouse_a.id == spouse_b.id:
            raise SelfMarriageException()

        if spouse_a.gender is spouse_b.gender:
            raise InvalidMarriageGenderException(
                detail=[f"both spouses are {spouse_a.gender.value}"]
            )

        cls._check_minimum_age(spouse_a, marriage_date)
        cls._check_minimum_age(spouse_b, marriage_date)

    @classmethod
    def _check_minimum_age(cls, person: Person, marriage_date: date) -> None:
        age = person.age(marriage_date)

        if age is not None and age < cls.MIN_MARRIAGE_AGE:
            raise UnderageMarriageException(
                detail=[f"{person.name} is under the legal marriage age."]
            )
