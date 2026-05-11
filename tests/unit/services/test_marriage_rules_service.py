from datetime import date

import pytest

from app.domain.entities.person import Gender, Person
from app.domain.exceptions.marriage_exceptions import (
    InvalidMarriageGenderException,
    SelfMarriageException,
    UnderageMarriageException,
)
from app.domain.services.marriage_rules import MarriageRulesService


def create_person(**overrides):
    return Person(
        id=overrides.get("id", 1),
        name=overrides.get("name", "Ali"),
        gender=overrides.get("gender", Gender.MALE),
        birth_date=overrides.get("birth_date", date(2000, 1, 1)),
        father_id=overrides.get("father_id"),
        mother_id=overrides.get("mother_id"),
    )


def test_validate_marriage_success():
    husband = create_person(id=1, gender=Gender.MALE, birth_date=date(1995, 1, 1))
    wife = create_person(
        id=2, name="Sara", gender=Gender.FEMALE, birth_date=date(1997, 1, 1)
    )

    marriage_date = date(2023, 1, 1)

    MarriageRulesService.validate_marriage(husband, wife, marriage_date)


def test_validate_marriage_invalid_gender():
    husband = create_person(id=1, gender=Gender.FEMALE)
    wife = create_person(id=2, gender=Gender.FEMALE)

    marriage_date = date(2023, 1, 1)

    with pytest.raises(InvalidMarriageGenderException):
        MarriageRulesService.validate_marriage(husband, wife, marriage_date)


def test_validate_marriage_self_marriage():
    person = create_person(id=1)
    person2 = create_person(id=1)
    person2.gender = Gender.FEMALE

    marriage_date = date(2023, 1, 1)

    with pytest.raises(SelfMarriageException):
        MarriageRulesService.validate_marriage(person, person2, marriage_date)


def test_validate_marriage_underage():
    husband = create_person(id=1, birth_date=date(2010, 1, 1))
    wife = create_person(
        id=2, name="Sara", gender=Gender.FEMALE, birth_date=date(1997, 1, 1)
    )

    marriage_date = date(2023, 1, 1)

    with pytest.raises(UnderageMarriageException):
        MarriageRulesService.validate_marriage(husband, wife, marriage_date)
