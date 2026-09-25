from datetime import date

from app.domain.entities.person import Person
from app.domain.exceptions.marriage_exceptions import (
    InvalidMarriageGenderException,
    SelfMarriageException,
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

        Under-minimum age is not a hard block — historical trees often record
        marriages below today's legal age. Callers that want a soft alarm use
        ``underage_spouse_names`` / preview warnings instead.

        Raises:
            SelfMarriageException:
                If both spouses are the same person.
            InvalidMarriageGenderException:
                If both spouses have the same gender.
        """
        if spouse_a.id == spouse_b.id:
            raise SelfMarriageException()

        if spouse_a.gender is spouse_b.gender:
            raise InvalidMarriageGenderException(
                detail=[f"both spouses are {spouse_a.gender.value}"]
            )

    @classmethod
    def underage_spouse_names(
        cls,
        spouse_a: Person,
        spouse_b: Person,
        marriage_date: date,
    ) -> list[str]:
        """Names of spouses younger than ``MIN_MARRIAGE_AGE`` on the wedding date."""
        names: list[str] = []
        for person in (spouse_a, spouse_b):
            age = person.age(marriage_date)
            if age is not None and age < cls.MIN_MARRIAGE_AGE:
                names.append(person.name)
        return names
