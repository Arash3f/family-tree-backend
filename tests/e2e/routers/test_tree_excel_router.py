from datetime import date
from io import BytesIO
from json import dumps
from uuid import UUID

import pytest
from openpyxl import Workbook

from app.application.services.tree_excel_service import (
    MARRIAGE_HEADERS,
    PERSON_HEADERS,
)
from app.domain.entities.person import Gender, Person
from tests.e2e.auth_headers import admin_headers as admin_headers
from tests.helpers.uow import TreeUnitOfWork


def excel_url(tree_id: UUID, suffix: str) -> str:
    return f"/family-trees/{tree_id}/excel{suffix}"


def _workbook(
    *, people: list[list[object]], marriages: list[list[object]] | None = None
) -> bytes:
    workbook = Workbook()
    workbook.active.title = "Instructions"
    persons = workbook.create_sheet("Persons")
    for index, header in enumerate(PERSON_HEADERS, start=1):
        persons.cell(row=1, column=index, value=header)
    for row_index, row in enumerate(people, start=2):
        for col_index, value in enumerate(row, start=1):
            persons.cell(row=row_index, column=col_index, value=value)
    marriages_ws = workbook.create_sheet("Marriages")
    for index, header in enumerate(MARRIAGE_HEADERS, start=1):
        marriages_ws.cell(row=1, column=index, value=header)
    for row_index, row in enumerate(marriages or [], start=2):
        for col_index, value in enumerate(row, start=1):
            marriages_ws.cell(row=row_index, column=col_index, value=value)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _xlsx_files(content: bytes, name: str = "tree.xlsx"):
    return {
        "file": (
            name,
            content,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }


@pytest.mark.asyncio
async def test_sample_excel_has_no_id_column(client, tree_id, admin_headers):  # noqa: F811
    from openpyxl import load_workbook

    resp = await client.get(excel_url(tree_id, "/sample"), headers=admin_headers)
    assert resp.status_code == 200
    workbook = load_workbook(BytesIO(resp.content), data_only=True)
    person_headers = [
        cell.value for cell in workbook["Persons"][1] if cell.value is not None
    ]
    marriage_headers = [
        cell.value for cell in workbook["Marriages"][1] if cell.value is not None
    ]
    assert "id" not in person_headers
    assert "id" not in marriage_headers


@pytest.mark.asyncio
async def test_sample_excel_uses_accept_language(client, tree_id, admin_headers):  # noqa: F811
    from openpyxl import load_workbook

    headers = {**admin_headers, "Accept-Language": "fa-IR"}
    resp = await client.get(excel_url(tree_id, "/sample"), headers=headers)
    assert resp.status_code == 200
    assert "family-tree-sample-fa.xlsx" in resp.headers.get("content-disposition", "")
    workbook = load_workbook(BytesIO(resp.content), data_only=True)
    assert workbook["Instructions"]["A1"].value == "قالب اکسل شجره‌نامه"
    assert workbook["Persons"]["B2"].value == "علی"

    resp_en = await client.get(excel_url(tree_id, "/sample"), headers=admin_headers)
    assert resp_en.status_code == 200
    assert "family-tree-sample-en.xlsx" in resp_en.headers.get(
        "content-disposition", ""
    )
    workbook_en = load_workbook(BytesIO(resp_en.content), data_only=True)
    assert workbook_en["Instructions"]["A1"].value == "Family Tree Excel template"
    assert workbook_en["Persons"]["B2"].value == "Ali"


@pytest.mark.asyncio
async def test_preview_marks_people_already_in_the_tree(
    client, tree_id, admin_headers, uow: TreeUnitOfWork
):  # noqa: F811
    await uow.persons.create(
        Person(
            tree_id=uow.tree_id,
            id=None,
            name="Ali",
            family_name="Karimi",
            gender=Gender.MALE,
            birth_date=date(1970, 1, 1),
        )
    )
    await uow.commit()

    content = _workbook(
        people=[
            ["P1", "Ali", "Karimi", "male", "1970-01-01"],
            ["P2", "Reza", "Karimi", "male", "1995-01-01"],
        ]
    )
    resp = await client.post(
        excel_url(tree_id, "/import/preview"),
        files=_xlsx_files(content),
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    by_ref = {person["ref"]: person for person in body["persons"]}
    assert by_ref["P1"]["already_exists"] is True
    assert "Ali Karimi" in (by_ref["P1"]["existing_label"] or "")
    assert by_ref["P2"]["already_exists"] is False
    assert body["valid"] is True


@pytest.mark.asyncio
async def test_import_skips_existing_and_only_creates_selected_people(
    client, tree_id, admin_headers, uow: TreeUnitOfWork
):  # noqa: F811
    await uow.persons.create(
        Person(
            tree_id=uow.tree_id,
            id=None,
            name="Ali",
            family_name="Karimi",
            gender=Gender.MALE,
            birth_date=date(1970, 1, 1),
        )
    )
    await uow.commit()

    content = _workbook(
        people=[
            ["P1", "Ali", "Karimi", "male", "1970-01-01"],
            ["P2", "Reza", "Karimi", "male", "1995-01-01"],
            ["P3", "Sara", "Ahmadi", "female", "1996-01-01"],
        ]
    )
    resp = await client.post(
        excel_url(tree_id, "/import"),
        files=_xlsx_files(content),
        data={"include": dumps({"person_refs": ["P2"], "marriage_refs": []})},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["persons_created"] == 1
    assert body["marriages_created"] == 0

    listed = await client.post(
        f"/family-trees/{tree_id}/persons/list",
        json={
            "filters": {},
            "pagination": {"offset": 0, "page": 1, "page_size": 30},
            "sort": {"sort_by": "name", "sort_order": "asc"},
        },
        headers=admin_headers,
    )
    assert listed.status_code == 200, listed.text
    names = {item["name"] for item in listed.json()["items"]}
    assert names == {"Ali", "Reza"}
