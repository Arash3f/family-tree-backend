"""A row that matches someone already in the tree is an edit, not a skip.

Before this, an import only ever created: a corrected family name on a row
carrying a system id was dropped silently, and on a row without one the same
person came back as a second row.
"""

from datetime import date
from uuid import UUID, uuid4

import pytest

from app.application.services.tree_excel_service import (
    UPDATABLE_PERSON_FIELDS,
    ExcelPersonRow,
    apply_person_row_changes,
    person_row_changes,
)
from app.domain.entities.person import Gender, Person
from app.domain.exceptions.person_exceptions import InvalidBirthDateException

TREE_ID = UUID(int=7)


def _person(**overrides) -> Person:
    defaults = {
        "id": uuid4(),
        "name": "Ali",
        "gender": Gender.MALE,
        "tree_id": TREE_ID,
        "family_name": "Karimi",
        "birth_date": date(1980, 5, 1),
        "birth_place": "Shiraz",
        "notes": "first note",
    }
    return Person(**{**defaults, **overrides})


def _row(**overrides) -> ExcelPersonRow:
    defaults = {
        "ref": "P1",
        "name": "Ali",
        "gender": Gender.MALE,
        "family_name": "Karimi",
        "birth_date": date(1980, 5, 1),
        "birth_place": "Shiraz",
        "notes": "first note",
    }
    return ExcelPersonRow(**{**defaults, **overrides})


def test_unchanged_row_reports_no_changes():
    assert person_row_changes(_person(), _row()) == {}


def test_changed_family_name_is_reported():
    assert person_row_changes(_person(), _row(family_name="Ahmadi")) == {
        "family_name": "Ahmadi"
    }


def test_every_updatable_field_is_detected():
    existing = _person(death_date=None, death_place=None)
    row = _row(
        name="Ali Reza",
        family_name="Ahmadi",
        gender=Gender.FEMALE,
        birth_date=date(1981, 6, 2),
        death_date=date(2020, 1, 1),
        birth_place="Tehran",
        death_place="Isfahan",
        notes="second note",
    )

    assert set(person_row_changes(existing, row)) == set(UPDATABLE_PERSON_FIELDS)


def test_blank_cell_never_clears_a_stored_value():
    """A hand-made sheet may simply not carry a column."""
    existing = _person(notes="keep me", birth_place="Shiraz")
    row = _row(notes=None, birth_place="   ")

    assert person_row_changes(existing, row) == {}


def test_surrounding_whitespace_is_not_a_change():
    assert person_row_changes(_person(), _row(family_name="  Karimi  ")) == {}


def test_apply_writes_the_changes_onto_the_entity():
    existing = _person()

    apply_person_row_changes(existing, {"family_name": "Ahmadi"})

    assert existing.family_name == "Ahmadi"


def test_apply_rejects_an_edit_that_breaks_an_invariant():
    existing = _person(birth_date=date(1980, 5, 1))

    with pytest.raises(InvalidBirthDateException):
        apply_person_row_changes(existing, {"death_date": date(1970, 1, 1)})
