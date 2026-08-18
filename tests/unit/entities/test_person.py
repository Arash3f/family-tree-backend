from datetime import date, timedelta
from uuid import UUID

import pytest

from app.domain.entities.person import (
    Gender,
    ParentLink,
    ParentRelationshipType,
    Person,
)
from app.domain.exceptions.common_exceptions import UnExpectedIdException
from app.domain.exceptions.person_exceptions import (
    InvalidBirthDateException,
    SameParentException,
    SelfParentException,
    TooManyBiologicalParentsException,
)

TEST_TREE_ID = UUID(int=1)


def create_person(**overrides):
    return Person(
        id=overrides.get("id", UUID(int=1)),
        name=overrides.get("name", "Ali"),
        gender=overrides.get("gender", Gender.MALE),
        tree_id=overrides.get("tree_id", TEST_TREE_ID),
        birth_date=overrides.get("birth_date", date(2000, 1, 1)),
        death_date=overrides.get("death_date"),
        parents=overrides.get("parents", []),
        marriage_id=overrides.get("marriage_id"),
    )


def test_death_date_cannot_be_before_birth_date():
    with pytest.raises(InvalidBirthDateException):
        create_person(
            birth_date=date(2000, 1, 1),
            death_date=date(1999, 1, 1),
        )


def test_birth_date_cannot_be_in_future():
    future_date = date.today() + timedelta(days=1)

    with pytest.raises(InvalidBirthDateException):
        create_person(birth_date=future_date)


def test_person_cannot_be_own_parent():
    with pytest.raises(SelfParentException):
        create_person(parents=[ParentLink(parent_id=UUID(int=1))])


def test_same_parent_not_allowed():
    with pytest.raises(SameParentException):
        create_person(
            parents=[
                ParentLink(parent_id=UUID(int=2)),
                ParentLink(parent_id=UUID(int=2)),
            ]
        )


def test_too_many_biological_parents_not_allowed():
    with pytest.raises(TooManyBiologicalParentsException):
        create_person(
            parents=[
                ParentLink(parent_id=UUID(int=2)),
                ParentLink(parent_id=UUID(int=3)),
                ParentLink(parent_id=UUID(int=4)),
            ]
        )


def test_set_parents_successfully():
    person = create_person()

    person.set_parents([ParentLink(parent_id=UUID(int=10))])

    assert person.parent_ids == [UUID(int=10)]


def test_add_parent_successfully():
    person = create_person(parents=[ParentLink(parent_id=UUID(int=10))])

    person.add_parent(
        ParentLink(
            parent_id=UUID(int=20),
            relationship_type=ParentRelationshipType.ADOPTIVE,
        )
    )

    assert person.parent_ids == [UUID(int=10), UUID(int=20)]


def test_set_parents_cannot_include_self():
    person = create_person(id=UUID(int=5))

    with pytest.raises(SelfParentException):
        person.set_parents([ParentLink(parent_id=UUID(int=5))])


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
    father = create_person(id=UUID(int=1))
    child = create_person(id=UUID(int=2), parents=[ParentLink(parent_id=UUID(int=1))])

    assert father.is_parent_of(child) is True


def test_is_child_of():
    father = create_person(id=UUID(int=1))
    child = create_person(id=UUID(int=2), parents=[ParentLink(parent_id=UUID(int=1))])

    assert child.is_child_of(father) is True


def test_is_sibling_of_true():
    p1 = create_person(id=UUID(int=1), parents=[ParentLink(parent_id=UUID(int=10))])
    p2 = create_person(id=UUID(int=2), parents=[ParentLink(parent_id=UUID(int=10))])

    assert p1.is_sibling_of(p2) is True


def test_is_sibling_of_false_if_same_person():
    p1 = create_person(id=UUID(int=1))

    assert p1.is_sibling_of(p1) is False


def test_safe_id_returns_id():
    person = create_person(id=UUID(int=10))

    assert person.safe_id == UUID(int=10)


def test_safe_id_raises_if_none():
    person = create_person(id=None)

    with pytest.raises(UnExpectedIdException):
        _ = person.safe_id
