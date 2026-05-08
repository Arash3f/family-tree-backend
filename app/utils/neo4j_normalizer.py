from datetime import datetime, date, time
from typing import Any


def normalize_neo4j_value(value: Any) -> Any:
    # Primitive
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    # List
    if isinstance(value, list):
        return [normalize_neo4j_value(v) for v in value]

    # Dict
    if isinstance(value, dict):
        return {str(k): normalize_neo4j_value(v) for k, v in value.items()}

    # Extract attributes safely
    year = getattr(value, "year", None)
    month = getattr(value, "month", None)
    day = getattr(value, "day", None)
    hour = getattr(value, "hour", None)
    minute = getattr(value, "minute", None)
    second = getattr(value, "second", None)
    micro = getattr(value, "microsecond", None)
    tz = getattr(value, "tzinfo", None)

    # Fix float second
    if isinstance(second, float):
        sec_int = int(second)
        micro = int((second - sec_int) * 1_000_000)
        second = sec_int

    # Date
    if year is not None and month is not None and day is not None and hour is None:
        return date(year, month, day)

    # Datetime
    if year is not None and month is not None and day is not None:
        return datetime(
            year,
            month,
            day,
            hour or 0,
            minute or 0,
            second or 0,
            micro or 0,
            tz,
        )

    # Time
    if hour is not None or minute is not None:
        return time(
            hour or 0,
            minute or 0,
            second or 0,
            micro or 0,
            tz,
        )

    return str(value)
