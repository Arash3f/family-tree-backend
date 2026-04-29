from datetime import date

import jdatetime


def jalali_to_gregorian(jalali_str: str) -> date:
    """
    Convert a Jalali (Persian) date string to a Gregorian date.

    The input date must be in the format "YYYY/MM/DD".

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
    year, month, day = map(int, jalali_str.split("/"))
    j_date = jdatetime.date(year, month, day)
    g_date = j_date.togregorian()
    return g_date


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
