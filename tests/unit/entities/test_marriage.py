from uuid import UUID
from datetime import date

import pytest

from app.domain.entities.marriage import Marriage
from app.domain.exceptions.common_exceptions import UnExpectedIdException
from app.domain.exceptions.marriage_exceptions import (
    DivorceBeforeMarriageException,
    MarriageAfterDivorceException,
    MarriageAlreadyDivorcedException,
    SelfMarriageException,
)


TEST_TREE_ID = UUID(int=1)


def create_marriage(**overrides):
    return Marriage(
        id=overrides.get("id", UUID(int=1)),
        tree_id=overrides.get("tree_id", TEST_TREE_ID),
        divorced_at=overrides.get("divorced_at", None),
        married_at=overrides.get("married_at", date(2020, 1, 1)),
        spouse_a_id=overrides.get("spouse_a_id", UUID(int=1)),
        spouse_b_id=overrides.get("spouse_b_id", UUID(int=2)),
    )


def test_cannot_marry_self():
    with pytest.raises(SelfMarriageException):
        create_marriage(spouse_a_id=UUID(int=1), spouse_b_id=UUID(int=1))


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


def test_divorce_rejects_an_already_divorced_marriage():
    marriage = create_marriage(divorced_at=date(2022, 1, 1))

    with pytest.raises(MarriageAlreadyDivorcedException):
        marriage.divorce(date(2023, 1, 1))

    assert marriage.divorced_at == date(2022, 1, 1)


def test_set_divorced_at_corrects_an_existing_divorce_date():
    marriage = create_marriage(divorced_at=date(2022, 1, 1))

    marriage.set_divorced_at(date(2023, 1, 1))

    assert marriage.divorced_at == date(2023, 1, 1)


def test_set_divorced_at_still_rejects_a_date_before_the_marriage():
    marriage = create_marriage()

    with pytest.raises(DivorceBeforeMarriageException):
        marriage.set_divorced_at(date(2019, 1, 1))


def test_clear_divorce_reactivates_the_marriage():
    marriage = create_marriage(divorced_at=date(2022, 1, 1))

    marriage.clear_divorce()

    assert marriage.divorced_at is None
    assert marriage.is_active() is True


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
    marriage = create_marriage(id=UUID(int=10))

    assert marriage.safe_id == UUID(int=10)


def test_safe_id_raises_if_none():
    marriage = create_marriage(id=None)

    with pytest.raises(UnExpectedIdException):
        _ = marriage.safe_id


def test_safe_divorced_at_returns_date():
    marriage = create_marriage(divorced_at=date(2022, 1, 1))

    assert marriage.safe_divorced_at == date(2022, 1, 1)


def test_safe_divorced_at_raises_if_none():
    marriage = create_marriage()

    with pytest.raises(RuntimeError):
        _ = marriage.safe_divorced_at
