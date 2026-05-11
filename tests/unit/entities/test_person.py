from datetime import date, timedelta

import pytest

from app.domain.entities.person import Gender, Person
from app.domain.exceptions.common_exceptions import UnExpectedIdException
from app.domain.exceptions.person_exceptions import (
    InvalidBirthDateException,
    SameParentException,
    SelfParentException,
)


def create_person(**overrides):
    return Person(
        id=overrides.get("id", 1),
        name=overrides.get("name", "Ali"),
        gender=overrides.get("gender", Gender.MALE),
        birth_date=overrides.get("birth_date", date(2000, 1, 1)),
        father_id=overrides.get("father_id", None),
        mother_id=overrides.get("mother_id", None),
    )


def test_birth_date_cannot_be_in_future():
    future_date = date.today() + timedelta(days=1)

    with pytest.raises(InvalidBirthDateException):
        create_person(birth_date=future_date)


def test_person_cannot_be_own_parent():
    with pytest.raises(SelfParentException):
        create_person(father_id=1)


def test_same_parent_not_allowed():
    with pytest.raises(SameParentException):
        create_person(father_id=2, mother_id=2)


def test_set_father_successfully():
    person = create_person()

    person.set_father(10)

    assert person.father_id == 10


def test_set_mother_successfully():
    person = create_person()

    person.set_mother(20)

    assert person.mother_id == 20


def test_set_father_cannot_be_self():
    person = create_person(id=5)

    with pytest.raises(SelfParentException):
        person.set_father(5)


def test_set_mother_cannot_be_self():
    person = create_person(id=5)

    with pytest.raises(SelfParentException):
        person.set_mother(5)


def test_set_father_cannot_be_same_as_mother():
    person = create_person(mother_id=7)

    with pytest.raises(SameParentException):
        person.set_father(7)


def test_set_mother_cannot_be_same_as_father():
    person = create_person(father_id=9)

    with pytest.raises(SameParentException):
        person.set_mother(9)


def test_age_returns_none_if_birthdate_missing():
    person = create_person(birth_date=None)

    assert person.age() is None


def test_age_calculation():
    person = create_person(birth_date=date(2000, 1, 1))

    age = person.age(on=date(2020, 1, 1))

    assert age == 20


def test_age_before_birthday():
    person = create_person(birth_date=date(2000, 5, 10))

    age = person.age(on=date(2020, 5, 1))

    assert age == 19


def test_is_parent_of():
    father = create_person(id=1)
    child = create_person(id=2, father_id=1)

    assert father.is_parent_of(child) is True


def test_is_child_of():
    father = create_person(id=1)
    child = create_person(id=2, father_id=1)

    assert child.is_child_of(father) is True


def test_is_sibling_of_true():
    p1 = create_person(id=1, father_id=10)
    p2 = create_person(id=2, father_id=10)

    assert p1.is_sibling_of(p2) is True


def test_is_sibling_of_false_if_same_person():
    p1 = create_person(id=1)

    assert p1.is_sibling_of(p1) is False


def test_safe_id_returns_id():
    person = create_person(id=10)

    assert person.safe_id == 10


def test_safe_id_raises_if_none():
    person = create_person(id=None)

    with pytest.raises(UnExpectedIdException):
        _ = person.safe_id
