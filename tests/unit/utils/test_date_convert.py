from datetime import date

import pytest

from app.presentation.utils.date_convert import gregorian_to_jalali, jalali_to_gregorian


def test_jalali_to_gregorian_and_back():
    g = jalali_to_gregorian("1403/01/15")
    assert g == date(2024, 4, 3)
    assert gregorian_to_jalali(g) == "1403/01/15"


def test_jalali_to_gregorian_invalid_format():
    with pytest.raises(ValueError):
        jalali_to_gregorian("1403-01-15")
