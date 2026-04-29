from datetime import date

from app.domain.entities.person import Gender, Person
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
        husband: Person,
        wife: Person,
        marriage_date: date,
    ) -> None:
        """
        Validate marriage between two persons according to business rules.

        Checks:
            - Husband must be male and wife must be female.
            - Husband and wife must not be the same person (no self-marriage).
            - Both parties must be at least the minimum legal marriage age on the marriage date.

        Args:
            husband (Person):
                The person acting as husband.
            wife (Person):
                The person acting as wife.
            marriage_date (date):
                The date of marriage, used for age validation.

        Raises:
            InvalidMarriageGenderException:
                If husband/wife have incorrect genders.
            SelfMarriageException:
                If husband and wife are the same person.
            UnderageMarriageException:
                If either party is under the minimum marriage age.
        """
        # Validate husband and wife genders!
        if husband.gender == Gender.FEMALE or wife.gender == Gender.MALE:
            raise InvalidMarriageGenderException()

        # Validate self marriage!
        if husband.id == wife.id:
            raise SelfMarriageException()

        # Validate husband and wife age by `min_marriage_age`
        cls._check_minimum_age(husband, marriage_date)
        cls._check_minimum_age(wife, marriage_date)

    @classmethod
    def _check_minimum_age(cls, person: Person, marriage_date: date) -> None:
        """
        Check if a person is at least the minimum legal marriage age.

        Args:
            person (Person):
                Person to validate.
            marriage_date (date):
                The date by which minimum age is calculated.

        Raises:
            UnderageMarriageException:
                If the person's age on marriage date is below `MIN_MARRIAGE_AGE`.
        """
        age = person.age(marriage_date)

        if age is not None and age < cls.MIN_MARRIAGE_AGE:
            raise UnderageMarriageException(
                detail=[f"{person.name} is under the legal marriage age."]
            )
