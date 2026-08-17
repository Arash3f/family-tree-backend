from datetime import date

import pytest

from app.presentation.utils.date_convert import gregorian_to_jalali, jalali_to_gregorian


def test_jalali_to_gregorian_and_back():
    g = jalali_to_gregorian("1403/01/15")
    assert g == date(2024, 4, 3)
    assert gregorian_to_jalali(g) == "1403/01/15"


def test_jalali_to_gregorian_invalid_format():
    with pytest.raises(ValueError):
        jalali_to_gregorian("1403")


def test_jalali_to_gregorian_accepts_dashes():
    assert jalali_to_gregorian("1403-01-15") == date(2024, 4, 3)


def test_parse_user_date_jalali_day_31():
    from app.presentation.utils.date_convert import parse_user_date

    assert parse_user_date("1403-06-31") == date(2024, 9, 21)
    assert parse_user_date("۱۴۰۳/۰۶/۳۱") == date(2024, 9, 21)


def test_parse_user_date_gregorian_iso():
    from app.presentation.utils.date_convert import parse_user_date

    assert parse_user_date("1965-02-20") == date(1965, 2, 20)
    assert parse_user_date("۱۹۶۵-۰۲-۲۰") == date(1965, 2, 20)


def test_jalali_to_gregorian_persian_digits():
    g = jalali_to_gregorian("۱۴۰۳/۰۱/۱۵")
    assert g == date(2024, 4, 3)


def test_to_ascii_digits():
    from app.presentation.utils.date_convert import to_ascii_digits

    assert to_ascii_digits("۱۹۶۵-۰۲-۲۰") == "1965-02-20"


def test_person_create_accepts_persian_iso_digits():
    from app.domain.entities.person import Gender
    from app.presentation.rest.schemas.dto.person_schema import PersonCreateRequest

    req = PersonCreateRequest.model_validate(
        {
            "name": "Ali",
            "gender": Gender.MALE,
            "birth_date": "۱۹۶۵-۰۲-۲۰",
        }
    )
    assert req.birth_date == date(1965, 2, 20)


def test_person_create_accepts_jalali_day_31():
    from app.domain.entities.person import Gender
    from app.presentation.rest.schemas.dto.person_schema import PersonCreateRequest

    req = PersonCreateRequest.model_validate(
        {
            "name": "Ali",
            "gender": Gender.MALE,
            "birth_date": "۱۴۰۳-۰۶-۳۱",
        }
    )
    assert req.birth_date == date(2024, 9, 21)
