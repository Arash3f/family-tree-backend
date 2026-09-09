import asyncio
import json
from urllib.parse import quote
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
from app.presentation.dependencies import (
    get_marriage_rules_service,
    get_request_uow,
)
from app.presentation.rest.dependencies.tree_guard import (
    require_tree_marriage_create,
    require_tree_person_create,
    require_tree_view,
    require_tree_view_birth_date,
    require_tree_view_marriage_date,
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
    warning: str | None = None
    parent1_label: str | None = None
    parent2_label: str | None = None
    marriage_label: str | None = None


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
    spouse_a_label: str | None = None
    spouse_b_label: str | None = None


class TreeExcelPreviewResponse(BaseModel):
    valid: bool
    persons: list[TreeExcelPreviewPerson]
    marriages: list[TreeExcelPreviewMarriage]
    errors: list[str]


def _ascii_fallback_name(filename: str) -> str:
    """A plain-ASCII name for clients that ignore RFC 5987 encoding.

    A fully Persian name has nothing to transliterate, so it falls back to a
    generic label rather than to a string of separators.
    """
    base = filename[: -len(".xlsx")] if filename.lower().endswith(".xlsx") else filename
    kept = [
        ch if (ch.isascii() and (ch.isalnum() or ch in ("-", "_"))) else "-"
        for ch in base
    ]
    collapsed = "-".join(part for part in "".join(kept).split("-") if part)
    return f"{collapsed or 'family-tree'}.xlsx"


def _xlsx_response(*, filename: str, content: bytes) -> Response:
    if not filename.lower().endswith(".xlsx"):
        filename = f"{filename}.xlsx"
    ascii_name = _ascii_fallback_name(filename)

    # RFC 5987: the ASCII name is a fallback, the encoded one is what a modern
    # browser saves, so a Persian tree name survives the download.
    encoded_name = quote(filename, safe="")

    return Response(
        content=content,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                f'attachment; filename="{ascii_name}"; '
                f"filename*=UTF-8''{encoded_name}"
            ),
        },
    )


_UPLOAD_MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "not_xlsx": (
            "Only Excel .xlsx files can be imported. In Excel choose "
            "“Save as” and pick the .xlsx format."
        ),
        "empty_file": "The uploaded file is empty.",
        "preview_timeout": (
            "Checking this file took longer than 60 seconds. Try splitting it "
            "into smaller files."
        ),
        "import_timeout": (
            "The import took longer than 5 minutes and was stopped. Try "
            "importing fewer rows at a time."
        ),
        "export_timeout": "The export took longer than 5 minutes and was stopped.",
        "bad_selection": "The list of selected rows could not be read.",
    },
    "fa": {
        "not_xlsx": (
            "فقط فایل اکسل با پسوند xlsx. قابل ورود است. در اکسل «ذخیره "
            "به‌نام» را بزنید و قالب xlsx. را انتخاب کنید."
        ),
        "empty_file": "فایلی که بارگذاری شد خالی است.",
        "preview_timeout": (
            "بررسی این فایل بیش از ۶۰ ثانیه طول کشید. آن را به فایل‌های کوچک‌تر "
            "تقسیم کنید."
        ),
        "import_timeout": (
            "ورود اطلاعات بیش از ۵ دقیقه طول کشید و متوقف شد. هر بار ردیف‌های "
            "کمتری را وارد کنید."
        ),
        "export_timeout": "خروجی گرفتن بیش از ۵ دقیقه طول کشید و متوقف شد.",
        "bad_selection": "فهرست ردیف‌های انتخاب‌شده خوانده نشد.",
    },
}


def _timeout_response(lang: str, key: str) -> Response:
    return Response(
        content=json.dumps(
            {"detail": _upload_message(lang, key)}, ensure_ascii=False
        ),
        status_code=504,
        media_type="application/json",
    )


def _upload_message(lang: str, key: str) -> str:
    catalog = _UPLOAD_MESSAGES.get(lang) or _UPLOAD_MESSAGES["en"]
    return catalog[key]


def _not_xlsx_message(lang: str) -> str:
    return _upload_message(lang, "not_xlsx")


def _empty_file_message(lang: str) -> str:
    return _upload_message(lang, "empty_file")


def _preview_timeout_message(lang: str) -> str:
    return _upload_message(lang, "preview_timeout")


def _parse_include(raw: str | None, lang: str) -> TreeExcelImportInclude | None:
    if raw is None or not raw.strip():
        return None
    try:
        return TreeExcelImportInclude.model_validate_json(raw)
    except ValidationError as exc:
        raise TreeExcelInvalidException(
            detail=[_upload_message(lang, "bad_selection")]
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
    lang = detect_language(request)
    try:
        usecase = ExportTreeExcelUseCase(uow)
        result = await asyncio.wait_for(
            usecase.execute(tree_id=tree_id, lang=lang),
            timeout=300.0,
        )
        return _xlsx_response(filename=result.filename, content=result.content)
    except TimeoutError:
        return _timeout_response(lang, "export_timeout")


@router.post(
    "/import/preview",
    response_model=TreeExcelPreviewResponse,
    dependencies=[
        Depends(require_tree_person_create),
        Depends(require_tree_marriage_create),
    ],
)
async def preview_excel_import(
    request: Request,
    tree_id: UUID,
    file: UploadFile = File(...),
    uow=Depends(get_request_uow),
    marriage_rule_service=Depends(get_marriage_rules_service),
) -> TreeExcelPreviewResponse:
    lang = detect_language(request)
    filename = (file.filename or "").lower()
    if not filename.endswith(".xlsx"):
        raise TreeExcelInvalidException(detail=[_not_xlsx_message(lang)])

    content = await file.read()
    if not content:
        raise TreeExcelInvalidException(detail=[_empty_file_message(lang)])

    try:
        usecase = PreviewTreeExcelUseCase(uow, marriage_rule_service)
        result = await asyncio.wait_for(
            usecase.execute(tree_id=tree_id, content=content, lang=lang),
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
            errors=[_preview_timeout_message(lang)],
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
    request: Request,
    tree_id: UUID,
    file: UploadFile = File(...),
    include: str | None = Form(default=None),
    uow=Depends(get_request_uow),
    marriage_rule_service=Depends(get_marriage_rules_service),
) -> TreeExcelImportResponse | Response:
    lang = detect_language(request)
    filename = (file.filename or "").lower()
    if not filename.endswith(".xlsx"):
        raise TreeExcelInvalidException(detail=[_not_xlsx_message(lang)])

    content = await file.read()
    if not content:
        raise TreeExcelInvalidException(detail=[_empty_file_message(lang)])

    selection = _parse_include(include, lang)
    try:
        usecase = ImportTreeExcelUseCase(uow, marriage_rule_service)
        result = await asyncio.wait_for(
            usecase.execute(
                tree_id=tree_id,
                content=content,
                person_refs=set(selection.person_refs) if selection else None,
                marriage_refs=set(selection.marriage_refs) if selection else None,
                lang=lang,
            ),
            timeout=300.0,
        )
        return TreeExcelImportResponse(
            persons_created=result.persons_created,
            marriages_created=result.marriages_created,
        )
    except TimeoutError:
        return _timeout_response(lang, "import_timeout")
