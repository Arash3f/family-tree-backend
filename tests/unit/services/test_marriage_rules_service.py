from uuid import UUID
from datetime import date

import pytest

from app.domain.entities.person import Gender, Person
from app.domain.exceptions.marriage_exceptions import (
    InvalidMarriageGenderException,
    SelfMarriageException,
    UnderageMarriageException,
)
from app.domain.services.marriage_rules import MarriageRulesService


TEST_TREE_ID = UUID(int=1)


def create_person(**overrides):
    return Person(
        id=overrides.get("id", UUID(int=1)),
        name=overrides.get("name", "Ali"),
        gender=overrides.get("gender", Gender.MALE),
        tree_id=overrides.get("tree_id", TEST_TREE_ID),
        birth_date=overrides.get("birth_date", date(2000, 1, 1)),
    )


def test_validate_marriage_success():
    spouse_a = create_person(
        id=UUID(int=1), gender=Gender.MALE, birth_date=date(1995, 1, 1)
    )
    spouse_b = create_person(
        id=UUID(int=2), name="Sara", gender=Gender.FEMALE, birth_date=date(1997, 1, 1)
    )

    marriage_date = date(2023, 1, 1)

    MarriageRulesService.validate_marriage(
        spouse_a=spouse_a, spouse_b=spouse_b, marriage_date=marriage_date
    )


def test_validate_marriage_self_marriage():
    person = create_person(id=UUID(int=1))
    person2 = create_person(id=UUID(int=1))
    person2.gender = Gender.FEMALE

    marriage_date = date(2023, 1, 1)

    with pytest.raises(SelfMarriageException):
        MarriageRulesService.validate_marriage(
            spouse_a=person, spouse_b=person2, marriage_date=marriage_date
        )


def test_validate_marriage_underage():
    spouse_a = create_person(id=UUID(int=1), birth_date=date(2010, 1, 1))
    spouse_b = create_person(
        id=UUID(int=2), name="Sara", gender=Gender.FEMALE, birth_date=date(1997, 1, 1)
    )

    marriage_date = date(2023, 1, 1)

    with pytest.raises(UnderageMarriageException):
        MarriageRulesService.validate_marriage(
            spouse_a=spouse_a, spouse_b=spouse_b, marriage_date=marriage_date
        )


@pytest.mark.parametrize("gender", [Gender.MALE, Gender.FEMALE])
def test_validate_marriage_rejects_same_gender(gender):
    spouse_a = create_person(id=UUID(int=1), gender=gender, birth_date=date(1995, 1, 1))
    spouse_b = create_person(
        id=UUID(int=2), name="Sam", gender=gender, birth_date=date(1996, 1, 1)
    )

    with pytest.raises(InvalidMarriageGenderException):
        MarriageRulesService.validate_marriage(
            spouse_a=spouse_a, spouse_b=spouse_b, marriage_date=date(2023, 1, 1)
        )
