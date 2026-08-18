import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, ValidationError

from app.application.use_cases.family_tree.export_tree_excel_use_case import (
    ExportTreeExcelUseCase,
)
from app.application.use_cases.family_tree.get_tree_excel_sample_use_case import (
    GetTreeExcelSampleUseCase,
)
from app.application.use_cases.family_tree.import_tree_excel_use_case import (
    ImportTreeExcelUseCase,
)
from app.application.use_cases.family_tree.preview_tree_excel_use_case import (
    PreviewTreeExcelUseCase,
)
from app.domain.exceptions.family_tree_exceptions import TreeExcelInvalidException
from app.presentation.rest.dependencies.tree_guard import (
    require_tree_marriage_create,
    require_tree_person_create,
    require_tree_view,
    require_tree_view_birth_date,
    require_tree_view_marriage_date,
)
from app.presentation.rest.utils.dependencies import (
    get_marriage_rules_service,
    get_request_uow,
)
from app.presentation.rest.utils.language import detect_language

router = APIRouter(prefix="/excel", tags=["Family Tree Excel"])


class TreeExcelImportResponse(BaseModel):
    persons_created: int
    marriages_created: int


class TreeExcelImportInclude(BaseModel):
    person_refs: list[str] = []
    marriage_refs: list[str] = []


class TreeExcelPreviewPerson(BaseModel):
    ref: str
    name: str
    family_name: str | None = None
    gender: str
    birth_date: str | None = None
    death_date: str | None = None
    parent1_ref: str | None = None
    parent2_ref: str | None = None
    marriage_ref: str | None = None
    row_number: int
    already_exists: bool = False
    existing_label: str | None = None
    duplicate_of_ref: str | None = None


class TreeExcelPreviewMarriage(BaseModel):
    ref: str
    spouse_a_ref: str
    spouse_b_ref: str
    married_at: str
    divorced_at: str | None = None
    row_number: int
    already_exists: bool = False
    duplicate_of_ref: str | None = None
    warning: str | None = None


class TreeExcelPreviewResponse(BaseModel):
    valid: bool
    persons: list[TreeExcelPreviewPerson]
    marriages: list[TreeExcelPreviewMarriage]
    errors: list[str]


def _xlsx_response(*, filename: str, content: bytes) -> Response:
    ascii_name = "".join(
        ch if (ch.isascii() and (ch.isalnum() or ch in ("-", "_", "."))) else "-"
        for ch in filename
    ).strip("-.")
    if not ascii_name.lower().endswith(".xlsx"):
        ascii_name = f"{ascii_name or 'family-tree'}.xlsx"

    return Response(
        content=content,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": f'attachment; filename="{ascii_name}"',
        },
    )


def _parse_include(raw: str | None) -> TreeExcelImportInclude | None:
    if raw is None or not raw.strip():
        return None
    try:
        return TreeExcelImportInclude.model_validate_json(raw)
    except ValidationError as exc:
        raise TreeExcelInvalidException(
            detail=["Invalid include payload for Excel import"]
        ) from exc


@router.get(
    "/sample",
    dependencies=[Depends(require_tree_view)],
)
async def download_excel_sample(
    request: Request,
    tree_id: UUID,
    uow=Depends(get_request_uow),
) -> Response:
    usecase = GetTreeExcelSampleUseCase(uow)
    result = await usecase.execute(tree_id=tree_id, lang=detect_language(request))
    return _xlsx_response(filename=result.filename, content=result.content)


@router.get(
    "/export",
    dependencies=[
        Depends(require_tree_view),
        Depends(require_tree_view_birth_date),
        Depends(require_tree_view_marriage_date),
    ],
)
async def export_excel(
    request: Request,
    tree_id: UUID,
    uow=Depends(get_request_uow),
) -> Response:
    try:
        usecase = ExportTreeExcelUseCase(uow)
        result = await asyncio.wait_for(
            usecase.execute(tree_id=tree_id, lang=detect_language(request)),
            timeout=300.0,
        )
        return _xlsx_response(filename=result.filename, content=result.content)
    except TimeoutError:
        return Response(
            content='{"detail": "Excel export timed out after 5 minutes"}',
            status_code=504,
            media_type="application/json",
        )


@router.post(
    "/import/preview",
    response_model=TreeExcelPreviewResponse,
    dependencies=[
        Depends(require_tree_person_create),
        Depends(require_tree_marriage_create),
    ],
)
async def preview_excel_import(
    tree_id: UUID,
    file: UploadFile = File(...),
    uow=Depends(get_request_uow),
    marriage_rule_service=Depends(get_marriage_rules_service),
) -> TreeExcelPreviewResponse:
    filename = (file.filename or "").lower()
    if not filename.endswith(".xlsx"):
        raise TreeExcelInvalidException(detail=["Only .xlsx Excel files are supported"])

    content = await file.read()
    if not content:
        raise TreeExcelInvalidException(detail=["Uploaded file is empty"])

    try:
        usecase = PreviewTreeExcelUseCase(uow, marriage_rule_service)
        result = await asyncio.wait_for(
            usecase.execute(tree_id=tree_id, content=content),
            timeout=60.0,
        )
        return TreeExcelPreviewResponse(
            valid=result.valid,
            persons=[
                TreeExcelPreviewPerson(**person.__dict__) for person in result.persons
            ],
            marriages=[
                TreeExcelPreviewMarriage(**marriage.__dict__)
                for marriage in result.marriages
            ],
            errors=result.errors,
        )
    except TimeoutError:
        return TreeExcelPreviewResponse(
            valid=False,
            persons=[],
            marriages=[],
            errors=["Excel preview timed out after 60 seconds"],
        )


@router.post(
    "/import",
    response_model=TreeExcelImportResponse,
    dependencies=[
        Depends(require_tree_person_create),
        Depends(require_tree_marriage_create),
    ],
)
async def import_excel(
    tree_id: UUID,
    file: UploadFile = File(...),
    include: str | None = Form(default=None),
    uow=Depends(get_request_uow),
    marriage_rule_service=Depends(get_marriage_rules_service),
) -> TreeExcelImportResponse | Response:
    filename = (file.filename or "").lower()
    if not filename.endswith(".xlsx"):
        raise TreeExcelInvalidException(detail=["Only .xlsx Excel files are supported"])

    content = await file.read()
    if not content:
        raise TreeExcelInvalidException(detail=["Uploaded file is empty"])

    selection = _parse_include(include)
    try:
        usecase = ImportTreeExcelUseCase(uow, marriage_rule_service)
        result = await asyncio.wait_for(
            usecase.execute(
                tree_id=tree_id,
                content=content,
                person_refs=set(selection.person_refs) if selection else None,
                marriage_refs=set(selection.marriage_refs) if selection else None,
            ),
            timeout=300.0,
        )
        return TreeExcelImportResponse(
            persons_created=result.persons_created,
            marriages_created=result.marriages_created,
        )
    except TimeoutError:
        return Response(
            content='{"detail": "Excel import timed out after 5 minutes"}',
            status_code=504,
            media_type="application/json",
        )
