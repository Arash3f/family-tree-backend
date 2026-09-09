from datetime import date
from io import BytesIO
from uuid import uuid4

import pytest
from openpyxl import Workbook, load_workbook

from app.application.services.tree_excel_service import (
    MARRIAGE_HEADERS,
    MARRIAGE_HEADERS_FA,
    PERSON_HEADERS,
    PERSON_HEADERS_FA,
    ExcelMarriageRow,
    ExcelPersonRow,
    ParsedTreeExcel,
    build_export_workbook,
    build_sample_workbook,
    match_tree_excel,
    parse_tree_excel,
)
from app.domain.entities.marriage import Marriage
from app.domain.entities.person import Gender, ParentLink, Person
from app.domain.exceptions.family_tree_exceptions import TreeExcelInvalidException
from app.presentation.utils.date_convert import gregorian_to_jalali


def test_excel_headers_do_not_include_id():
    assert "id" not in PERSON_HEADERS
    assert "id" not in MARRIAGE_HEADERS
    assert "id" not in PERSON_HEADERS_FA
    assert "id" not in MARRIAGE_HEADERS_FA


def test_sample_workbook_has_no_id_column():
    workbook = load_workbook(BytesIO(build_sample_workbook()), data_only=True)
    person_headers = [
        cell.value for cell in workbook["Persons"][1] if cell.value is not None
    ]
    marriage_headers = [
        cell.value for cell in workbook["Marriages"][1] if cell.value is not None
    ]
    assert person_headers == PERSON_HEADERS
    assert marriage_headers == MARRIAGE_HEADERS


def test_sample_workbook_fa_has_persian_sheets_headers_and_data():
    workbook = load_workbook(BytesIO(build_sample_workbook(lang="fa")), data_only=True)
    assert workbook["راهنما"]["A1"].value == "شجره‌نامه — قالب اکسل"
    assert workbook["افراد"]["B2"].value == "علی"
    assert workbook["افراد"]["C2"].value == "کریمی"
    assert workbook["افراد"]["D2"].value == "مرد"
    person_headers = [
        cell.value for cell in workbook["افراد"][1] if cell.value is not None
    ]
    marriage_headers = [
        cell.value for cell in workbook["ازدواج‌ها"][1] if cell.value is not None
    ]
    assert person_headers == PERSON_HEADERS_FA
    assert marriage_headers == MARRIAGE_HEADERS_FA
    assert workbook["ازدواج‌ها"]["F2"].value == "1334/03/10"
    parsed = parse_tree_excel(build_sample_workbook(lang="fa"))
    assert [person.ref for person in parsed.persons] == ["P1", "P2", "P3", "P4", "P5"]
    assert parsed.persons[0].gender == Gender.MALE
    assert parsed.persons[0].birth_date == date(1951, 3, 22)


def test_sample_workbook_fa_sheets_read_right_to_left():
    workbook = load_workbook(BytesIO(build_sample_workbook(lang="fa")))
    assert workbook["افراد"].sheet_view.rightToLeft is True
    assert workbook["راهنما"].sheet_view.rightToLeft is True
    english = load_workbook(BytesIO(build_sample_workbook(lang="en")))
    assert english["Persons"].sheet_view.rightToLeft is False


def test_sample_workbook_spells_out_parents_next_to_their_codes():
    workbook = load_workbook(BytesIO(build_sample_workbook(lang="fa")), data_only=True)
    persons = workbook["افراد"]
    # Row 4 is Reza, child of Ali (P1) and Zahra (P2).
    assert persons["J4"].value == "P1"
    assert persons["K4"].value == "علی کریمی"
    assert persons["M4"].value == "P2"
    assert persons["N4"].value == "زهرا کریمی"
    assert persons["Q4"].value == "علی کریمی × زهرا کریمی"
    marriages = workbook["ازدواج‌ها"]
    assert marriages["C2"].value == "علی کریمی"
    assert marriages["E2"].value == "زهرا کریمی"


def test_sample_workbook_en_has_english_instructions_and_data():
    workbook = load_workbook(BytesIO(build_sample_workbook(lang="en")), data_only=True)
    assert workbook["Instructions"]["A1"].value == "Family tree — Excel template"
    assert workbook["Persons"]["B2"].value == "Ali"
    assert workbook["Persons"]["C2"].value == "Karimi"


def test_code_dropdowns_point_at_the_other_sheet_without_a_leading_equals():
    # Excel offers to "repair" a workbook whose validation range starts with
    # '=', which would scare a user off before they ever see the template.
    workbook = load_workbook(BytesIO(build_sample_workbook(lang="fa")))
    formulas = {
        validation.formula1
        for sheet in ("افراد", "ازدواج‌ها")
        for validation in workbook[sheet].data_validations.dataValidation
    }
    range_formulas = {formula for formula in formulas if "!" in formula}

    assert range_formulas
    for formula in range_formulas:
        assert not formula.startswith("=")
    assert "'افراد'!$A$2:$A$2000" in range_formulas
    assert "'ازدواج‌ها'!$A$2:$A$2000" in range_formulas


def test_instructions_sheet_explains_every_column():
    workbook = load_workbook(BytesIO(build_sample_workbook(lang="fa")), data_only=True)
    legend = {
        row[0].value: row[1].value
        for row in workbook["راهنما"].iter_rows(min_col=1, max_col=2)
        if row[0].value
    }
    for header in (*PERSON_HEADERS_FA, *MARRIAGE_HEADERS_FA):
        assert legend.get(header), header


def test_parse_tree_excel_accepts_workbook_without_id():
    parsed = parse_tree_excel(build_sample_workbook())
    assert [person.ref for person in parsed.persons] == ["P1", "P2", "P3", "P4", "P5"]
    assert [marriage.ref for marriage in parsed.marriages] == ["M1", "M2"]


def test_export_workbook_has_no_id_column():
    tree_id = uuid4()
    person = Person(
        id=uuid4(),
        name="Ali",
        family_name="Karimi",
        gender=Gender.MALE,
        tree_id=tree_id,
        birth_date=date(1951, 3, 22),
    )
    content = build_export_workbook(persons=[person], marriages=[])
    workbook = load_workbook(BytesIO(content), data_only=True)
    headers = [cell.value for cell in workbook["Persons"][1] if cell.value is not None]
    assert "id" not in headers
    assert headers == PERSON_HEADERS
    assert workbook["Persons"]["E2"].value == "1951-03-22"


def test_export_workbook_fa_uses_persian_headers_and_jalali_dates():
    tree_id = uuid4()
    person = Person(
        id=uuid4(),
        name="علی",
        family_name="کریمی",
        gender=Gender.MALE,
        tree_id=tree_id,
        birth_date=date(1951, 3, 22),
    )
    content = build_export_workbook(persons=[person], marriages=[], lang="fa")
    workbook = load_workbook(BytesIO(content), data_only=True)
    headers = [cell.value for cell in workbook["افراد"][1] if cell.value is not None]
    assert headers == PERSON_HEADERS_FA
    assert workbook["افراد"]["D2"].value == "مرد"
    assert workbook["افراد"]["E2"].value == gregorian_to_jalali(date(1951, 3, 22))
    parsed = parse_tree_excel(content)
    assert parsed.persons[0].birth_date == date(1951, 3, 22)
    assert parsed.persons[0].gender == Gender.MALE


def test_match_tree_excel_keeps_in_file_namesakes_separate():
    tree_id = uuid4()
    existing_id = uuid4()
    existing = Person(
        id=existing_id,
        name="Ali",
        family_name="Karimi",
        gender=Gender.MALE,
        tree_id=tree_id,
        birth_date=date(1951, 3, 22),
    )
    parsed = ParsedTreeExcel(
        persons=[
            ExcelPersonRow(
                ref="P1",
                name="Ali",
                family_name="Karimi",
                gender=Gender.MALE,
                birth_date=date(1951, 3, 22),
                row_number=2,
            ),
            ExcelPersonRow(
                ref="P2",
                name="Ali",
                family_name="Karimi",
                gender=Gender.MALE,
                birth_date=date(1951, 3, 22),
                row_number=3,
            ),
            ExcelPersonRow(
                ref="P3",
                name="Reza",
                gender=Gender.MALE,
                row_number=4,
            ),
        ]
    )

    match = match_tree_excel(parsed, [existing], [])

    assert match.person_existing_id["P1"] == existing_id
    # First row consumes the unique existing match; the in-file namesake stays new.
    assert "P2" not in match.person_existing_id
    assert "P2" not in match.person_duplicate_of
    assert match.person_namesake_of["P2"] == "P1"
    assert "P3" not in match.person_existing_id
    assert "P3" not in match.person_namesake_of


def test_match_tree_excel_skips_ambiguous_existing_identity():
    tree_id = uuid4()
    first = Person(
        id=uuid4(),
        name="Ali",
        family_name="Karimi",
        gender=Gender.MALE,
        tree_id=tree_id,
        birth_date=None,
    )
    second = Person(
        id=uuid4(),
        name="Ali",
        family_name="Karimi",
        gender=Gender.MALE,
        tree_id=tree_id,
        birth_date=None,
    )
    parsed = ParsedTreeExcel(
        persons=[
            ExcelPersonRow(
                ref="P1",
                name="Ali",
                family_name="Karimi",
                gender=Gender.MALE,
                birth_date=None,
                row_number=2,
            ),
        ]
    )

    match = match_tree_excel(parsed, [first, second], [])

    assert "P1" not in match.person_existing_id
    assert "P1" in match.person_ambiguous_identity
    assert match.person_warning("P1") is not None


def test_match_tree_excel_prefers_uuid_ref_over_name_identity():
    tree_id = uuid4()
    target_id = uuid4()
    other_id = uuid4()
    target = Person(
        id=target_id,
        name="Ali",
        family_name="Karimi",
        gender=Gender.MALE,
        tree_id=tree_id,
        birth_date=None,
    )
    other = Person(
        id=other_id,
        name="Ali",
        family_name="Karimi",
        gender=Gender.MALE,
        tree_id=tree_id,
        birth_date=None,
    )
    parsed = ParsedTreeExcel(
        persons=[
            ExcelPersonRow(
                ref=str(target_id),
                name="Ali",
                family_name="Karimi",
                gender=Gender.MALE,
                birth_date=None,
                row_number=2,
            ),
        ]
    )

    match = match_tree_excel(parsed, [target, other], [])

    assert match.person_existing_id[str(target_id)] == target_id
    assert str(target_id) not in match.person_ambiguous_identity


def test_match_tree_excel_detects_existing_marriage():
    tree_id = uuid4()
    husband_id = uuid4()
    wife_id = uuid4()
    marriage_id = uuid4()
    husband = Person(
        id=husband_id,
        name="Ali",
        gender=Gender.MALE,
        tree_id=tree_id,
        birth_date=date(1970, 1, 1),
    )
    wife = Person(
        id=wife_id,
        name="Zahra",
        gender=Gender.FEMALE,
        tree_id=tree_id,
        birth_date=date(1972, 1, 1),
    )
    marriage = Marriage(
        id=marriage_id,
        tree_id=tree_id,
        spouse_a_id=husband_id,
        spouse_b_id=wife_id,
        married_at=date(1995, 6, 1),
    )

    parsed = ParsedTreeExcel(
        persons=[
            ExcelPersonRow(
                ref="P1",
                name="Ali",
                gender=Gender.MALE,
                birth_date=date(1970, 1, 1),
                row_number=2,
            ),
            ExcelPersonRow(
                ref="P2",
                name="Zahra",
                gender=Gender.FEMALE,
                birth_date=date(1972, 1, 1),
                row_number=3,
            ),
        ],
        marriages=[
            ExcelMarriageRow(
                ref="M1",
                spouse_a_ref="P1",
                spouse_b_ref="P2",
                married_at=date(1995, 6, 1),
                row_number=2,
            )
        ],
    )

    match = match_tree_excel(parsed, [husband, wife], [marriage])

    assert match.marriage_existing_id["M1"] == marriage_id


def test_parse_ignores_legacy_id_column_if_present():
    workbook = Workbook()
    workbook.active.title = "Instructions"
    persons = workbook.create_sheet("Persons")
    headers = [*PERSON_HEADERS, "id"]
    for index, header in enumerate(headers, start=1):
        persons.cell(row=1, column=index, value=header)
    persons.cell(row=2, column=1, value="P1")
    persons.cell(row=2, column=2, value="Ali")
    persons.cell(row=2, column=4, value="male")
    persons.cell(row=2, column=len(headers), value=str(uuid4()))
    marriages = workbook.create_sheet("Marriages")
    for index, header in enumerate(MARRIAGE_HEADERS, start=1):
        marriages.cell(row=1, column=index, value=header)
    buffer = BytesIO()
    workbook.save(buffer)

    parsed = parse_tree_excel(buffer.getvalue())
    assert [person.ref for person in parsed.persons] == ["P1"]
    assert parsed.persons[0].name == "Ali"


def _workbook_with_person_rows(rows: list[list], headers=None) -> bytes:
    """Build a minimal workbook whose Persons sheet holds the given rows."""
    workbook = Workbook()
    workbook.active.title = "Instructions"
    persons = workbook.create_sheet("Persons")
    for index, header in enumerate(headers or PERSON_HEADERS, start=1):
        persons.cell(row=1, column=index, value=header)
    for row_offset, row in enumerate(rows, start=2):
        for col_index, value in enumerate(row, start=1):
            persons.cell(row=row_offset, column=col_index, value=value)
    marriages = workbook.create_sheet("Marriages")
    for index, header in enumerate(MARRIAGE_HEADERS, start=1):
        marriages.cell(row=1, column=index, value=header)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_parse_reports_every_bad_cell_in_one_pass():
    content = _workbook_with_person_rows(
        [
            ["P1", "Ali", "", "wizard"],
            ["P2", "", "", "male"],
            ["P3", "Reza", "", "male", "yesterday"],
            ["P1", "Sara", "", "female"],
        ]
    )

    parsed = parse_tree_excel(content)

    # One upload, four problems: the user fixes them all before trying again.
    assert len(parsed.errors) == 4
    assert [person.ref for person in parsed.persons] == []
    joined = " ".join(parsed.errors)
    assert "wizard" in joined
    assert "yesterday" in joined
    assert "row 5" in joined


def test_parse_errors_are_persian_and_name_the_persian_column():
    content = _workbook_with_person_rows([["P1", "Ali", "", "wizard"]])

    parsed = parse_tree_excel(content, lang="fa")

    assert len(parsed.errors) == 1
    message = parsed.errors[0]
    assert "برگهٔ «افراد»" in message
    assert "جنسیت" in message
    assert "مرد" in message


def test_parse_invents_a_code_when_the_column_is_left_empty():
    content = _workbook_with_person_rows(
        [
            ["", "Ali", "", "male"],
            ["R3", "Reza", "", "male"],
            ["", "Sara", "", "female"],
        ]
    )

    parsed = parse_tree_excel(content)

    refs = [person.ref for person in parsed.persons]
    assert refs[1] == "R3"
    assert len(set(refs)) == 3
    # A generated code never steals one the user typed further down.
    assert refs[0] != "R3"
    assert not parsed.errors


def test_parse_reads_the_system_id_column():
    person_id = uuid4()
    row = [""] * len(PERSON_HEADERS)
    row[0] = "P1"
    row[1] = "Ali"
    row[3] = "male"
    row[-1] = str(person_id)

    parsed = parse_tree_excel(_workbook_with_person_rows([row]))

    assert parsed.persons[0].ref == "P1"
    assert parsed.persons[0].system_id == person_id


def test_export_uses_short_codes_and_keeps_uuids_in_the_system_id_column():
    tree_id = uuid4()
    father_id = uuid4()
    child_id = uuid4()
    father = Person(
        id=father_id,
        name="Ali",
        family_name="Karimi",
        gender=Gender.MALE,
        tree_id=tree_id,
        birth_date=date(1951, 3, 22),
    )
    child = Person(
        id=child_id,
        name="Reza",
        family_name="Karimi",
        gender=Gender.MALE,
        tree_id=tree_id,
        birth_date=date(1979, 6, 10),
    )
    child.set_parents([ParentLink(parent_id=father_id)])

    content = build_export_workbook(persons=[father, child], marriages=[])
    persons = load_workbook(BytesIO(content), data_only=True)["Persons"]

    assert persons["A2"].value == "P1"
    assert persons["A3"].value == "P2"
    assert persons["J3"].value == "P1"
    assert persons["K3"].value == "Ali Karimi"
    assert persons["R2"].value == str(father_id)
    assert persons["R3"].value == str(child_id)


def test_reimporting_an_export_matches_on_the_system_id_column():
    tree_id = uuid4()
    person_id = uuid4()
    person = Person(
        id=person_id,
        name="Ali",
        family_name="Karimi",
        gender=Gender.MALE,
        tree_id=tree_id,
        birth_date=date(1951, 3, 22),
    )

    content = build_export_workbook(persons=[person], marriages=[])
    parsed = parse_tree_excel(content)
    match = match_tree_excel(parsed, [person], [])

    assert parsed.persons[0].ref == "P1"
    assert match.person_existing_id["P1"] == person_id


def test_system_id_wins_over_a_matching_name_in_the_tree():
    tree_id = uuid4()
    target_id = uuid4()
    namesake_id = uuid4()
    target = Person(
        id=target_id,
        name="Ali",
        family_name="Karimi",
        gender=Gender.MALE,
        tree_id=tree_id,
        birth_date=None,
    )
    namesake = Person(
        id=namesake_id,
        name="Ali",
        family_name="Karimi",
        gender=Gender.MALE,
        tree_id=tree_id,
        birth_date=None,
    )
    parsed = ParsedTreeExcel(
        persons=[
            ExcelPersonRow(
                ref="P1",
                name="Ali",
                family_name="Karimi",
                gender=Gender.MALE,
                system_id=target_id,
                row_number=2,
            )
        ]
    )

    match = match_tree_excel(parsed, [target, namesake], [])

    assert match.person_existing_id["P1"] == target_id
    assert "P1" not in match.person_ambiguous_identity


def test_missing_sheet_error_is_worded_for_the_reader():
    workbook = Workbook()
    workbook.active.title = "Sheet1"
    buffer = BytesIO()
    workbook.save(buffer)

    with pytest.raises(TreeExcelInvalidException) as excinfo:
        parse_tree_excel(buffer.getvalue(), lang="fa")

    assert "افراد" in excinfo.value.detail[0]
    assert "نمونه" in excinfo.value.detail[0]
