from datetime import date, datetime, time
from types import SimpleNamespace

from app.infrastructure.utils.neo4j_normalizer import normalize_neo4j_value


def test_normalize_primitives_and_none():
    assert normalize_neo4j_value(None) is None
    assert normalize_neo4j_value("x") == "x"
    assert normalize_neo4j_value(1) == 1
    assert normalize_neo4j_value(1.5) == 1.5
    assert normalize_neo4j_value(True) is True


def test_normalize_list_and_dict():
    assert normalize_neo4j_value([1, "a"]) == [1, "a"]
    assert normalize_neo4j_value({1: "a"}) == {"1": "a"}


def test_normalize_date_like():
    value = SimpleNamespace(year=2024, month=4, day=3)
    assert normalize_neo4j_value(value) == date(2024, 4, 3)


def test_normalize_datetime_with_float_seconds():
    value = SimpleNamespace(
        year=2024,
        month=4,
        day=3,
        hour=12,
        minute=30,
        second=1.5,
        microsecond=None,
        tzinfo=None,
    )
    result = normalize_neo4j_value(value)
    assert result == datetime(2024, 4, 3, 12, 30, 1, 500000)


def test_normalize_time_only():
    value = SimpleNamespace(hour=8, minute=15, second=0, microsecond=0, tzinfo=None)
    assert normalize_neo4j_value(value) == time(8, 15, 0, 0)


def test_normalize_fallback_str():
    class Marker:
        def __str__(self) -> str:
            return "marker"

    assert normalize_neo4j_value(Marker()) == "marker"
