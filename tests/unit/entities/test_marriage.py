from datetime import date

import pytest

from app.domain.entities.marriage import Marriage
from app.domain.exceptions.marriage_exceptions import (
    DivorceBeforeMarriageException,
    MarriageAfterDivorceException,
    SelfMarriageException,
)


def create_marriage(**overrides):
    return Marriage(
        id=overrides.get("id", 1),
        divorced_at=overrides.get("divorced_at", None),
        married_at=overrides.get("married_at", date(2020, 1, 1)),
        husband_id=overrides.get("husband_id", 1),
        wife_id=overrides.get("wife_id", 2),
    )


def test_cannot_marry_self():
    with pytest.raises(SelfMarriageException):
        create_marriage(husband_id=1, wife_id=1)


def test_divorce_before_marriage_not_allowed_on_creation():
    with pytest.raises(DivorceBeforeMarriageException):
        create_marriage(
            married_at=date(2020, 1, 1),
            divorced_at=date(2019, 1, 1),
        )


def test_divorce_before_marriage_not_allowed():
    marriage = create_marriage()

    with pytest.raises(DivorceBeforeMarriageException):
        marriage.divorce(divorced_at=date(2019, 1, 1))


def test_divorce_sets_divorce_date():
    marriage = create_marriage()

    marriage.divorce(date(2022, 1, 1))

    assert marriage.divorced_at == date(2022, 1, 1)


def test_marriage_date_cannot_be_after_divorce():
    marriage = create_marriage(
        divorced_at=date(2021, 1, 1),
    )

    with pytest.raises(MarriageAfterDivorceException):
        marriage.set_married_at(date(2022, 1, 1))


def test_set_married_at_updates_date():
    marriage = create_marriage()

    marriage.set_married_at(date(2019, 1, 1))

    assert marriage.married_at == date(2019, 1, 1)


def test_is_active_returns_true_when_not_divorced():
    marriage = create_marriage()

    assert marriage.is_active() is True


def test_is_active_returns_false_when_divorced():
    marriage = create_marriage(divorced_at=date(2022, 1, 1))

    assert marriage.is_active() is False


def test_safe_id_returns_id():
    marriage = create_marriage(id=10)

    assert marriage.safe_id == 10


def test_safe_id_raises_if_none():
    marriage = create_marriage(id=None)

    with pytest.raises(RuntimeError):
        _ = marriage.safe_id


def test_safe_divorced_at_returns_date():
    marriage = create_marriage(divorced_at=date(2022, 1, 1))

    assert marriage.safe_divorced_at == date(2022, 1, 1)


def test_safe_divorced_at_raises_if_none():
    marriage = create_marriage()

    with pytest.raises(RuntimeError):
        _ = marriage.safe_divorced_at
