from datetime import date, datetime

import jdatetime

_DIGIT_MAP = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
# Birth years in this app are Jalali 13xx/14xx, never Gregorian 1200-1500.
_JALALI_YEAR_MIN = 1200
_JALALI_YEAR_MAX = 1500


def to_ascii_digits(value: str) -> str:
    return value.translate(_DIGIT_MAP)


def _date_parts(value: str) -> tuple[int, int, int]:
    text = to_ascii_digits(value.strip()).replace(".", "-").replace("/", "-")
    parts = text.split("-")
    if len(parts) != 3:
        raise ValueError(f"invalid date: {value}")
    try:
        year, month, day = (int(part) for part in parts)
    except ValueError as exc:
        raise ValueError(f"invalid date: {value}") from exc
    if year < 1 or month < 1 or month > 12 or day < 1 or day > 31:
        raise ValueError(f"invalid date: {value}")
    return year, month, day


def jalali_to_gregorian(jalali_str: str) -> date:
    """
    Convert a Jalali (Persian) date string to a Gregorian date.

    Accepts ``YYYY/MM/DD`` or ``YYYY-MM-DD``, including Persian digits.

    Args:
        jalali_str (str): Jalali date string (e.g., "1403/01/15").

    Returns:
        date: Equivalent Gregorian date.

    Raises:
        ValueError: If the input string format is invalid or the date is not valid.

    Example:
        >>> jalali_to_gregorian("1403/01/15")
        datetime.date(2024, 4, 3)
    """
    year, month, day = _date_parts(jalali_str)
    return jdatetime.date(year, month, day).togregorian()


def parse_user_date(value: str | date | datetime | None) -> date | None:
    """Parse an API date that may be Gregorian ISO or Jalali."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return value
    text = to_ascii_digits(value.strip())
    if not text:
        return None
    year, month, day = _date_parts(text)
    if _JALALI_YEAR_MIN <= year <= _JALALI_YEAR_MAX:
        return jdatetime.date(year, month, day).togregorian()
    return date(year, month, day)


def gregorian_to_jalali(g_date: date) -> str:
    """
    Convert a Gregorian date to a Jalali (Persian) date string.

    The output format is "YYYY/MM/DD".

    Args:
        g_date (date): Gregorian date object.

    Returns:
        str: Jalali date string.

    Example:
        >>> gregorian_to_jalali(date(2024, 4, 3))
        "1403/01/15"
    """
    j_date = jdatetime.date.fromgregorian(date=g_date)
    return j_date.strftime("%Y/%m/%d")
