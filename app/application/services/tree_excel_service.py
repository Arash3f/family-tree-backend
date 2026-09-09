from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from io import BytesIO
from typing import Any
from uuid import UUID

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter, quote_sheetname
from openpyxl.worksheet.datavalidation import DataValidation

from app.domain.entities.marriage import Marriage
from app.domain.entities.person import (
    Gender,
    ParentRelationshipType,
    Person,
)
from app.domain.exceptions.family_tree_exceptions import TreeExcelInvalidException
from app.presentation.utils.date_convert import gregorian_to_jalali, parse_user_date

PERSONS_SHEET = "Persons"
MARRIAGES_SHEET = "Marriages"
INSTRUCTIONS_SHEET = "Instructions"

PERSONS_SHEET_FA = "افراد"
MARRIAGES_SHEET_FA = "ازدواج‌ها"
INSTRUCTIONS_SHEET_FA = "راهنما"

PERSONS_SHEET_ALIASES = (PERSONS_SHEET, PERSONS_SHEET_FA)
MARRIAGES_SHEET_ALIASES = (MARRIAGES_SHEET, MARRIAGES_SHEET_FA)

# Column order, shared by the sample, the export, and the import parser.
PERSON_COLUMNS = (
    "ref",
    "name",
    "family_name",
    "gender",
    "birth_date",
    "death_date",
    "birth_place",
    "death_place",
    "notes",
    "parent1_ref",
    "parent1_name",
    "parent1_type",
    "parent2_ref",
    "parent2_name",
    "parent2_type",
    "marriage_ref",
    "marriage_label",
    "system_id",
)

MARRIAGE_COLUMNS = (
    "ref",
    "spouse_a_ref",
    "spouse_a_name",
    "spouse_b_ref",
    "spouse_b_name",
    "married_at",
    "divorced_at",
    "system_id",
)

# Written for humans to read, never read back: the codes next to them carry
# the meaning, so a stale name here can never corrupt an import.
PERSON_DISPLAY_COLUMNS = frozenset(
    {"parent1_name", "parent2_name", "marriage_label"}
)
MARRIAGE_DISPLAY_COLUMNS = frozenset({"spouse_a_name", "spouse_b_name"})

PERSON_REQUIRED_COLUMNS = ("name", "gender")
MARRIAGE_REQUIRED_COLUMNS = ("spouse_a_ref", "spouse_b_ref", "married_at")

_PERSON_HEADER_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "ref": "code",
        "name": "first name",
        "family_name": "family name",
        "gender": "gender",
        "birth_date": "birth date",
        "death_date": "death date",
        "birth_place": "birth place",
        "death_place": "death place",
        "notes": "notes",
        "parent1_ref": "parent 1 code",
        "parent1_name": "parent 1 (name)",
        "parent1_type": "parent 1 type",
        "parent2_ref": "parent 2 code",
        "parent2_name": "parent 2 (name)",
        "parent2_type": "parent 2 type",
        "marriage_ref": "born from marriage (code)",
        "marriage_label": "born from marriage (couple)",
        "system_id": "system id (do not edit)",
    },
    "fa": {
        "ref": "کد",
        "name": "نام",
        "family_name": "نام خانوادگی",
        "gender": "جنسیت",
        "birth_date": "تاریخ تولد",
        "death_date": "تاریخ فوت",
        "birth_place": "محل تولد",
        "death_place": "محل فوت",
        "notes": "یادداشت",
        "parent1_ref": "کد والد ۱",
        "parent1_name": "والد ۱ (نام)",
        "parent1_type": "نوع والد ۱",
        "parent2_ref": "کد والد ۲",
        "parent2_name": "والد ۲ (نام)",
        "parent2_type": "نوع والد ۲",
        "marriage_ref": "کد ازدواج مبدأ",
        "marriage_label": "ازدواج مبدأ (زوج)",
        "system_id": "شناسه سیستمی (دست نزنید)",
    },
}

_MARRIAGE_HEADER_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "ref": "code",
        "spouse_a_ref": "spouse 1 code",
        "spouse_a_name": "spouse 1 (name)",
        "spouse_b_ref": "spouse 2 code",
        "spouse_b_name": "spouse 2 (name)",
        "married_at": "marriage date",
        "divorced_at": "divorce date",
        "system_id": "system id (do not edit)",
    },
    "fa": {
        "ref": "کد",
        "spouse_a_ref": "کد همسر ۱",
        "spouse_a_name": "همسر ۱ (نام)",
        "spouse_b_ref": "کد همسر ۲",
        "spouse_b_name": "همسر ۲ (نام)",
        "married_at": "تاریخ ازدواج",
        "divorced_at": "تاریخ طلاق",
        "system_id": "شناسه سیستمی (دست نزنید)",
    },
}

# Headers older exports and hand-written files used; still accepted on import.
_PERSON_LEGACY_HEADERS: dict[str, tuple[str, ...]] = {
    "ref": ("ref", "شناسه"),
    "name": ("name",),
    "family_name": ("family_name",),
    "gender": (),
    "birth_date": ("birth_date", "تولد"),
    "death_date": ("death_date", "فوت"),
    "birth_place": ("birth_place",),
    "death_place": ("death_place",),
    "notes": ("notes",),
    "parent1_ref": ("parent1_ref", "شناسه والد ۱", "شناسه والد 1", "کد والد 1"),
    "parent1_name": ("parent1_name",),
    "parent1_type": ("parent1_type", "نوع والد 1"),
    "parent2_ref": ("parent2_ref", "شناسه والد ۲", "شناسه والد 2", "کد والد 2"),
    "parent2_name": ("parent2_name",),
    "parent2_type": ("parent2_type", "نوع والد 2"),
    "marriage_ref": ("marriage_ref", "شناسه ازدواج", "ازدواج مبدأ"),
    "marriage_label": ("marriage_label",),
    "system_id": ("system_id", "system id", "uuid", "شناسه سیستمی"),
}

_MARRIAGE_LEGACY_HEADERS: dict[str, tuple[str, ...]] = {
    "ref": ("ref", "شناسه"),
    "spouse_a_ref": (
        "spouse_a_ref",
        "شناسه همسر ۱",
        "شناسه همسر 1",
        "همسر ۱",
        "همسر 1",
        "کد همسر 1",
    ),
    "spouse_a_name": ("spouse_a_name",),
    "spouse_b_ref": (
        "spouse_b_ref",
        "شناسه همسر ۲",
        "شناسه همسر 2",
        "همسر ۲",
        "همسر 2",
        "کد همسر 2",
    ),
    "spouse_b_name": ("spouse_b_name",),
    "married_at": ("married_at",),
    "divorced_at": ("divorced_at",),
    "system_id": ("system_id", "system id", "uuid", "شناسه سیستمی"),
}


def _build_aliases(
    columns: tuple[str, ...],
    labels: dict[str, dict[str, str]],
    legacy: dict[str, tuple[str, ...]],
) -> dict[str, frozenset[str]]:
    aliases: dict[str, frozenset[str]] = {}
    for key in columns:
        names = {key}
        for locale_labels in labels.values():
            names.add(locale_labels[key])
        names.update(legacy.get(key, ()))
        aliases[key] = frozenset(names)
    return aliases


_PERSON_HEADER_ALIASES = _build_aliases(
    PERSON_COLUMNS, _PERSON_HEADER_LABELS, _PERSON_LEGACY_HEADERS
)
_MARRIAGE_HEADER_ALIASES = _build_aliases(
    MARRIAGE_COLUMNS, _MARRIAGE_HEADER_LABELS, _MARRIAGE_LEGACY_HEADERS
)

_GENDER_ALIASES: dict[str, frozenset[str]] = {
    Gender.MALE.value: frozenset({"male", "man", "m", "مرد", "آقا", "پسر"}),
    Gender.FEMALE.value: frozenset({"female", "woman", "f", "زن", "خانم", "دختر"}),
}

_REL_TYPE_ALIASES: dict[str, frozenset[str]] = {
    ParentRelationshipType.BIOLOGICAL.value: frozenset(
        {"biological", "بیولوژیک", "تنی", "خونی"}
    ),
    ParentRelationshipType.ADOPTIVE.value: frozenset(
        {"adoptive", "فرزندخواندگی", "فرزند خواندگی"}
    ),
    ParentRelationshipType.STEP.value: frozenset({"step", "ناتنی"}),
}

_GENDER_LABELS: dict[str, dict[Gender, str]] = {
    "en": {Gender.MALE: "male", Gender.FEMALE: "female"},
    "fa": {Gender.MALE: "مرد", Gender.FEMALE: "زن"},
}

_REL_TYPE_LABELS: dict[str, dict[ParentRelationshipType, str]] = {
    "en": {
        ParentRelationshipType.BIOLOGICAL: "biological",
        ParentRelationshipType.ADOPTIVE: "adoptive",
        ParentRelationshipType.STEP: "step",
    },
    "fa": {
        ParentRelationshipType.BIOLOGICAL: "بیولوژیک",
        ParentRelationshipType.ADOPTIVE: "فرزندخواندگی",
        ParentRelationshipType.STEP: "ناتنی",
    },
}

# Kept as module constants because tests and older callers import them.
PERSON_HEADERS = [_PERSON_HEADER_LABELS["en"][key] for key in PERSON_COLUMNS]
MARRIAGE_HEADERS = [_MARRIAGE_HEADER_LABELS["en"][key] for key in MARRIAGE_COLUMNS]
PERSON_HEADERS_FA = [_PERSON_HEADER_LABELS["fa"][key] for key in PERSON_COLUMNS]
MARRIAGE_HEADERS_FA = [_MARRIAGE_HEADER_LABELS["fa"][key] for key in MARRIAGE_COLUMNS]

HEADER_FILL = PatternFill("solid", fgColor="0D6E67")
HEADER_FONT = Font(color="FFFFFF", bold=True)
SAMPLE_FILL = PatternFill("solid", fgColor="E8F5F3")
DISPLAY_FILL = PatternFill("solid", fgColor="F4F4F5")
DISPLAY_FONT = Font(color="6B7280", italic=True)
TITLE_FONT = Font(bold=True, size=14, color="0D6E67")
LEGEND_KEY_FONT = Font(bold=True)
THIN_BORDER = Border(
    left=Side(style="thin", color="D4D4D8"),
    right=Side(style="thin", color="D4D4D8"),
    top=Side(style="thin", color="D4D4D8"),
    bottom=Side(style="thin", color="D4D4D8"),
)

_COLUMN_WIDTHS: dict[str, int] = {
    "ref": 10,
    "name": 18,
    "family_name": 18,
    "gender": 12,
    "birth_date": 14,
    "death_date": 14,
    "birth_place": 16,
    "death_place": 16,
    "notes": 32,
    "parent1_ref": 12,
    "parent1_name": 22,
    "parent1_type": 16,
    "parent2_ref": 12,
    "parent2_name": 22,
    "parent2_type": 16,
    "marriage_ref": 14,
    "marriage_label": 28,
    "spouse_a_ref": 14,
    "spouse_a_name": 22,
    "spouse_b_ref": 14,
    "spouse_b_name": 22,
    "married_at": 14,
    "divorced_at": 14,
    "system_id": 38,
}

# Dropdowns and helper formatting reach this far down so a user can keep typing
# below the rows we wrote without losing the guard rails.
VALIDATION_LAST_ROW = 2000


def _normalize_locale(lang: str | None) -> str:
    return "fa" if (lang or "").lower().startswith("fa") else "en"


def _alias_lookup(aliases: dict[str, frozenset[str]]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for canonical, names in aliases.items():
        for name in names:
            lookup[name.casefold()] = canonical
    return lookup


_PERSON_HEADER_LOOKUP = _alias_lookup(_PERSON_HEADER_ALIASES)
_MARRIAGE_HEADER_LOOKUP = _alias_lookup(_MARRIAGE_HEADER_ALIASES)
_GENDER_LOOKUP = _alias_lookup(_GENDER_ALIASES)
_REL_TYPE_LOOKUP = _alias_lookup(_REL_TYPE_ALIASES)


_ERROR_TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "row_prefix": "Sheet “{sheet}”, row {row}: ",
        "unreadable": (
            "This file could not be opened as an Excel workbook. Save it as .xlsx, "
            "or start again from the sample file."
        ),
        "missing_sheet": (
            "This workbook has no sheet named “{sheet}”. Download the sample file "
            "and fill in its sheets instead of creating your own."
        ),
        "missing_columns": (
            "Sheet “{sheet}” is missing these columns: {columns}. Download the "
            "sample file to get the right headers."
        ),
        "name_required": "the “{column}” column is empty, so this row was skipped.",
        "duplicate_ref": (
            "the code “{ref}” is already used by row {other}. Every row needs its "
            "own code."
        ),
        "gender_invalid": (
            "“{column}” is “{value}”, which is not understood. Write one of: "
            "{options}."
        ),
        "gender_required": "“{column}” is empty. Write one of: {options}.",
        "rel_type_invalid": (
            "“{column}” is “{value}”, which is not understood. Leave it empty or "
            "write one of: {options}."
        ),
        "date_invalid": (
            "“{column}” is “{value}”, which is not a date we can read. Use "
            "{hint} — or leave the cell empty."
        ),
        "married_at_required": "“{column}” is empty, and every marriage needs one.",
        "spouse_required": (
            "“{column_a}” and “{column_b}” are both required, so this row was "
            "skipped."
        ),
        "unknown_parent": (
            "“{column}” points to code “{ref}”, which no row of sheet “{sheet}” "
            "uses."
        ),
        "unknown_marriage": (
            "“{column}” points to code “{ref}”, which no row of sheet “{sheet}” "
            "uses."
        ),
        "unknown_spouse": (
            "“{column}” points to code “{ref}”, which no row of sheet “{sheet}” "
            "uses, and nobody by that code is in the tree yet."
        ),
        "bio_parents_marriage": (
            "the biological parents must be the same two people as the couple in "
            "“{column}”."
        ),
        "date_hint": "2019-04-23 (Gregorian) or 1398/02/03 (Jalali)",
        "namesake": (
            "Same name, family name, gender, and birth date as code “{ref}” in this "
            "file. Both are imported as separate people."
        ),
        "ambiguous_identity": (
            "More than one person in this tree has this exact name and birth date, "
            "so we cannot tell which one you mean. This row will be added as a new "
            "person; to update an existing one instead, export the tree and reuse "
            "its “system id” value."
        ),
    },
    "fa": {
        "row_prefix": "برگهٔ «{sheet}»، ردیف {row}: ",
        "unreadable": (
            "این فایل به‌عنوان کارپوشهٔ اکسل باز نشد. آن را با قالب xlsx. ذخیره "
            "کنید یا از فایل نمونه شروع کنید."
        ),
        "missing_sheet": (
            "در این فایل برگه‌ای با نام «{sheet}» نیست. فایل نمونه را دانلود کنید "
            "و همان برگه‌ها را پر کنید."
        ),
        "missing_columns": (
            "در برگهٔ «{sheet}» این ستون‌ها نیست: {columns}. برای داشتن تیترهای "
            "درست، فایل نمونه را دانلود کنید."
        ),
        "name_required": "ستون «{column}» خالی است، پس این ردیف رد شد.",
        "duplicate_ref": (
            "کد «{ref}» قبلاً در ردیف {other} استفاده شده است. هر ردیف باید کد "
            "خودش را داشته باشد."
        ),
        "gender_invalid": (
            "مقدار «{column}» برابر «{value}» است که شناخته نمی‌شود. یکی از این‌ها "
            "را بنویسید: {options}."
        ),
        "gender_required": (
            "ستون «{column}» خالی است. یکی از این‌ها را بنویسید: {options}."
        ),
        "rel_type_invalid": (
            "مقدار «{column}» برابر «{value}» است که شناخته نمی‌شود. آن را خالی "
            "بگذارید یا یکی از این‌ها را بنویسید: {options}."
        ),
        "date_invalid": (
            "مقدار «{column}» برابر «{value}» است و به‌عنوان تاریخ خوانده نمی‌شود. "
            "از قالب {hint} استفاده کنید — یا سلول را خالی بگذارید."
        ),
        "married_at_required": (
            "ستون «{column}» خالی است، در حالی که هر ازدواج به آن نیاز دارد."
        ),
        "spouse_required": (
            "ستون‌های «{column_a}» و «{column_b}» هر دو لازم‌اند، پس این ردیف رد شد."
        ),
        "unknown_parent": (
            "مقدار «{column}» به کد «{ref}» اشاره می‌کند که هیچ ردیفی در برگهٔ "
            "«{sheet}» آن را ندارد."
        ),
        "unknown_marriage": (
            "مقدار «{column}» به کد «{ref}» اشاره می‌کند که هیچ ردیفی در برگهٔ "
            "«{sheet}» آن را ندارد."
        ),
        "unknown_spouse": (
            "مقدار «{column}» به کد «{ref}» اشاره می‌کند که نه در برگهٔ «{sheet}» "
            "هست و نه کسی با آن کد در شجره وجود دارد."
        ),
        "bio_parents_marriage": (
            "والدین بیولوژیک باید همان دو نفرِ زوجِ ستون «{column}» باشند."
        ),
        "date_hint": "۱۳۹۸/۰۲/۰۳ (شمسی) یا 2019-04-23 (میلادی)",
        "namesake": (
            "نام، نام خانوادگی، جنسیت و تاریخ تولد این ردیف با کد «{ref}» در همین "
            "فایل یکسان است. هر دو به‌عنوان دو نفر جدا وارد می‌شوند."
        ),
        "ambiguous_identity": (
            "بیش از یک نفر در این شجره دقیقاً همین نام و تاریخ تولد را دارند، پس "
            "نمی‌توانیم تشخیص دهیم کدام را می‌خواهید. این ردیف به‌عنوان فرد جدید "
            "اضافه می‌شود؛ اگر می‌خواهید فرد موجود به‌روز شود، از شجره خروجی "
            "بگیرید و مقدار «شناسه سیستمی» را نگه دارید."
        ),
    },
}


@dataclass(frozen=True)
class ExcelText:
    """Locale-aware wording for the spreadsheet itself and its error messages."""

    lang: str

    @property
    def persons_sheet(self) -> str:
        return PERSONS_SHEET_FA if self.lang == "fa" else PERSONS_SHEET

    @property
    def marriages_sheet(self) -> str:
        return MARRIAGES_SHEET_FA if self.lang == "fa" else MARRIAGES_SHEET

    @property
    def instructions_sheet(self) -> str:
        return INSTRUCTIONS_SHEET_FA if self.lang == "fa" else INSTRUCTIONS_SHEET

    def person_header(self, key: str) -> str:
        return _PERSON_HEADER_LABELS[self.lang][key]

    def marriage_header(self, key: str) -> str:
        return _MARRIAGE_HEADER_LABELS[self.lang][key]

    def person_headers(self) -> list[str]:
        return [self.person_header(key) for key in PERSON_COLUMNS]

    def marriage_headers(self) -> list[str]:
        return [self.marriage_header(key) for key in MARRIAGE_COLUMNS]

    def gender_label(self, gender: Gender) -> str:
        return _GENDER_LABELS[self.lang][gender]

    def rel_type_label(self, rel_type: ParentRelationshipType) -> str:
        return _REL_TYPE_LABELS[self.lang][rel_type]

    def gender_options(self) -> list[str]:
        return [self.gender_label(gender) for gender in Gender]

    def rel_type_options(self) -> list[str]:
        return [
            self.rel_type_label(rel_type) for rel_type in ParentRelationshipType
        ]

    def message(self, key: str, **params: Any) -> str:
        return _ERROR_TEXTS[self.lang][key].format(**params)

    def persons_row(self, row_number: int, key: str, **params: Any) -> str:
        prefix = self.message(
            "row_prefix", sheet=self.persons_sheet, row=row_number
        )
        return prefix + self.message(key, **params)

    def marriages_row(self, row_number: int, key: str, **params: Any) -> str:
        prefix = self.message(
            "row_prefix", sheet=self.marriages_sheet, row=row_number
        )
        return prefix + self.message(key, **params)

    def persons_row_detail(self, row_number: int, detail: str) -> str:
        """Wrap a message that came from the domain layer, already worded."""
        return (
            self.message("row_prefix", sheet=self.persons_sheet, row=row_number)
            + detail
        )

    def marriages_row_detail(self, row_number: int, detail: str) -> str:
        return (
            self.message("row_prefix", sheet=self.marriages_sheet, row=row_number)
            + detail
        )


def excel_text(lang: str | None) -> ExcelText:
    return ExcelText(_normalize_locale(lang))


def format_excel_date(value: date | None, *, lang: str) -> str:
    if value is None:
        return ""
    if _normalize_locale(lang) == "fa":
        return gregorian_to_jalali(value)
    return value.isoformat()


@dataclass
class ExcelPersonRow:
    ref: str
    name: str
    gender: Gender
    family_name: str | None = None
    birth_date: date | None = None
    death_date: date | None = None
    birth_place: str | None = None
    death_place: str | None = None
    notes: str | None = None
    parent1_ref: str | None = None
    parent1_type: ParentRelationshipType = ParentRelationshipType.BIOLOGICAL
    parent2_ref: str | None = None
    parent2_type: ParentRelationshipType = ParentRelationshipType.BIOLOGICAL
    marriage_ref: str | None = None
    system_id: UUID | None = None
    row_number: int = 0

    @property
    def label(self) -> str:
        parts = [self.name]
        if self.family_name:
            parts.append(self.family_name)
        return " ".join(parts)


@dataclass
class ExcelMarriageRow:
    ref: str
    spouse_a_ref: str
    spouse_b_ref: str
    married_at: date
    divorced_at: date | None = None
    system_id: UUID | None = None
    row_number: int = 0


@dataclass
class ParsedTreeExcel:
    persons: list[ExcelPersonRow] = field(default_factory=list)
    marriages: list[ExcelMarriageRow] = field(default_factory=list)
    #: Every cell-level problem found, so one upload reports every fix needed.
    errors: list[str] = field(default_factory=list)


def _cell_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        # Excel hands back 3.0 for a cell the user typed as 3.
        return str(int(value))
    text = str(value).strip()
    return text or None


class _RowIssues:
    """Collects every problem in one row so the user sees them all at once."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def add(self, message: str) -> None:
        self.messages.append(message)

    def __bool__(self) -> bool:
        return bool(self.messages)


def _parse_date_cell(
    value: Any,
    *,
    column: str,
    issues: _RowIssues,
    text: ExcelText,
    row_number: int,
    sheet_row: str,
) -> date | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    raw = _cell_str(value)
    if not raw:
        return None

    try:
        parsed = parse_user_date(raw)
    except (ValueError, KeyError):
        parsed = None
    if parsed is None:
        issues.add(
            getattr(text, sheet_row)(
                row_number,
                "date_invalid",
                column=column,
                value=raw,
                hint=text.message("date_hint"),
            )
        )
    return parsed


def _parse_gender_cell(
    value: Any,
    *,
    issues: _RowIssues,
    text: ExcelText,
    row_number: int,
) -> Gender | None:
    raw = _cell_str(value)
    options = ", ".join(text.gender_options())
    column = text.person_header("gender")
    if not raw:
        issues.add(
            text.persons_row(
                row_number, "gender_required", column=column, options=options
            )
        )
        return None
    canonical = _GENDER_LOOKUP.get(raw.casefold())
    if canonical is None:
        issues.add(
            text.persons_row(
                row_number,
                "gender_invalid",
                column=column,
                value=raw,
                options=options,
            )
        )
        return None
    return Gender(canonical)


def _parse_rel_type_cell(
    value: Any,
    *,
    column: str,
    issues: _RowIssues,
    text: ExcelText,
    row_number: int,
) -> ParentRelationshipType:
    raw = _cell_str(value)
    if not raw:
        return ParentRelationshipType.BIOLOGICAL
    canonical = _REL_TYPE_LOOKUP.get(raw.casefold())
    if canonical is None:
        issues.add(
            text.persons_row(
                row_number,
                "rel_type_invalid",
                column=column,
                value=raw,
                options=", ".join(text.rel_type_options()),
            )
        )
        return ParentRelationshipType.BIOLOGICAL
    return ParentRelationshipType(canonical)


def _column_letter(columns: tuple[str, ...], key: str) -> str:
    return get_column_letter(columns.index(key) + 1)


def _style_header(ws, columns: tuple[str, ...], headers: list[str]) -> None:
    for index, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=index, value=header)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )
        cell.border = THIN_BORDER
        key = columns[index - 1]
        ws.column_dimensions[get_column_letter(index)].width = _COLUMN_WIDTHS.get(
            key, 16
        )
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "B2"
    last_column = get_column_letter(len(headers))
    ws.auto_filter.ref = f"A1:{last_column}1"


def _apply_sheet_view(ws, *, lang: str) -> None:
    ws.sheet_view.rightToLeft = lang == "fa"


def _shade_display_columns(
    ws,
    columns: tuple[str, ...],
    display_keys: frozenset[str],
    *,
    last_row: int,
) -> None:
    """Grey out the read-only helper columns so nobody edits them by mistake."""
    if last_row < 2:
        return
    for key in (*display_keys, "system_id"):
        letter = _column_letter(columns, key)
        for row in range(2, last_row + 1):
            cell = ws[f"{letter}{row}"]
            cell.fill = DISPLAY_FILL
            cell.font = DISPLAY_FONT


def _range_formula(sheet_title: str, columns: tuple[str, ...], key: str) -> str:
    """A cross-sheet list source.

    No leading ``=``: Excel treats a data-validation range formula that starts
    with one as corrupt and offers to repair the workbook.
    """
    letter = _column_letter(columns, key)
    return (
        f"{quote_sheetname(sheet_title)}!"
        f"${letter}$2:${letter}${VALIDATION_LAST_ROW}"
    )


def _add_list_validation(
    ws,
    *,
    formula: str,
    targets: list[str],
    error: str | None,
) -> None:
    validation = DataValidation(
        type="list",
        formula1=formula,
        allow_blank=True,
        showErrorMessage=error is not None,
    )
    if error is not None:
        validation.error = error
    for target in targets:
        validation.add(target)
    ws.add_data_validation(validation)


def _add_person_validations(ws, *, lang: str = "en") -> None:
    """Dropdowns for the closed-vocabulary columns and the code references."""
    locale = _normalize_locale(lang)
    text = ExcelText(locale)
    last = VALIDATION_LAST_ROW

    gender_letter = _column_letter(PERSON_COLUMNS, "gender")
    _add_list_validation(
        ws,
        formula=f'"{",".join(text.gender_options())}"',
        targets=[f"{gender_letter}2:{gender_letter}{last}"],
        error=(
            "از مرد یا زن استفاده کنید" if locale == "fa" else "Use male or female"
        ),
    )

    type_letters = [
        _column_letter(PERSON_COLUMNS, "parent1_type"),
        _column_letter(PERSON_COLUMNS, "parent2_type"),
    ]
    _add_list_validation(
        ws,
        formula=f'"{",".join(text.rel_type_options())}"',
        targets=[f"{letter}2:{letter}{last}" for letter in type_letters],
        error=(
            "از بیولوژیک، فرزندخواندگی یا ناتنی استفاده کنید"
            if locale == "fa"
            else "Use biological, adoptive, or step"
        ),
    )

    # Picking a parent from a dropdown of the codes on this very sheet. Typing a
    # code by hand still works, so a user filling rows top-down is never stuck.
    parent_letters = [
        _column_letter(PERSON_COLUMNS, "parent1_ref"),
        _column_letter(PERSON_COLUMNS, "parent2_ref"),
    ]
    _add_list_validation(
        ws,
        formula=_range_formula(ws.title, PERSON_COLUMNS, "ref"),
        targets=[f"{letter}2:{letter}{last}" for letter in parent_letters],
        error=None,
    )


def _add_marriage_ref_validation(ws, marriages_title: str) -> None:
    marriage_letter = _column_letter(PERSON_COLUMNS, "marriage_ref")
    _add_list_validation(
        ws,
        formula=_range_formula(marriages_title, MARRIAGE_COLUMNS, "ref"),
        targets=[f"{marriage_letter}2:{marriage_letter}{VALIDATION_LAST_ROW}"],
        error=None,
    )


def _add_marriage_validations(ws, persons_title: str) -> None:
    spouse_letters = [
        _column_letter(MARRIAGE_COLUMNS, "spouse_a_ref"),
        _column_letter(MARRIAGE_COLUMNS, "spouse_b_ref"),
    ]
    _add_list_validation(
        ws,
        formula=_range_formula(persons_title, PERSON_COLUMNS, "ref"),
        targets=[
            f"{letter}2:{letter}{VALIDATION_LAST_ROW}" for letter in spouse_letters
        ],
        error=None,
    )


_HOW_TO: dict[str, list[str]] = {
    "en": [
        "Fill the “{persons}” sheet first — one row per person. Every row needs "
        "a first name and a gender.",
        "The “{code}” column is just a short nickname for the row, like P1 or "
        "P2. You invent it, and you only need it when someone else points at "
        "this person. Leave it empty and we will make one up for you.",
        "To record a parent, write that parent’s code in “{parent_code}”. The "
        "grey “{parent_name}” column next to it is filled in for you when you "
        "export, so you can read the sheet without matching codes by eye.",
        "Fill the “{marriages}” sheet for couples: the two spouse codes plus "
        "the marriage date.",
        "For a child born inside a marriage, put that marriage’s code in "
        "“{marriage_code}”. Its biological parents must be that couple.",
        "Dates accept {hint}. Empty means unknown.",
        "Grey columns are written for you to read. We never read them back, so "
        "editing them changes nothing.",
        "Two people with the same name stay two people. Give each their own "
        "code.",
        "On import you get a preview and choose which rows to add. Rows already "
        "in the tree are marked and skipped.",
    ],
    "fa": [
        "اول برگهٔ «{persons}» را پر کنید — هر نفر یک ردیف. هر ردیف حتماً باید "
        "نام و جنسیت داشته باشد.",
        "ستون «{code}» فقط یک نام اختصاری برای همان ردیف است، مثل P1 یا P2. "
        "خودتان آن را انتخاب می‌کنید و تنها وقتی لازم است که ردیف دیگری به این "
        "شخص اشاره کند. اگر خالی بگذارید، خودمان برایش کد می‌سازیم.",
        "برای ثبت والد، کدِ آن والد را در «{parent_code}» بنویسید. ستون خاکستریِ "
        "«{parent_name}» کنارش هنگام خروجی گرفتن پر می‌شود تا بتوانید فایل را "
        "بدون تطبیق چشمی کدها بخوانید.",
        "برگهٔ «{marriages}» برای زوج‌ها است: کد دو همسر به‌همراه تاریخ ازدواج.",
        "برای فرزندی که حاصل یک ازدواج است، کد همان ازدواج را در "
        "«{marriage_code}» بگذارید. والدین بیولوژیکش باید همان زوج باشند.",
        "تاریخ‌ها با قالب {hint} پذیرفته می‌شوند. خالی یعنی نامعلوم.",
        "ستون‌های خاکستری فقط برای خواندنِ شما نوشته می‌شوند. ما هرگز آن‌ها را "
        "نمی‌خوانیم، پس تغییرشان هیچ اثری ندارد.",
        "دو نفر هم‌نام، دو نفر باقی می‌مانند. برای هرکدام کد جدا بگذارید.",
        "هنگام ورود، پیش‌نمایش می‌بینید و خودتان انتخاب می‌کنید کدام ردیف‌ها "
        "اضافه شوند. ردیف‌هایی که از قبل در شجره هستند علامت می‌خورند و رد "
        "می‌شوند.",
    ],
}

_PERSON_COLUMN_HELP: dict[str, dict[str, str]] = {
    "en": {
        "ref": "Optional. Short code for this row (P1, P2…). Only needed if "
        "another row points here.",
        "name": "Required. First name.",
        "family_name": "Optional.",
        "gender": "Required. male or female.",
        "birth_date": "Optional. Leave empty if unknown.",
        "death_date": "Optional. Leave empty for a living person.",
        "birth_place": "Optional.",
        "death_place": "Optional.",
        "notes": "Optional. Anything you want to remember.",
        "parent1_ref": "Optional. The code of the first parent.",
        "parent1_name": "Read-only. The first parent’s name, for your eyes.",
        "parent1_type": "Optional. biological (default), adoptive, or step.",
        "parent2_ref": "Optional. The code of the second parent.",
        "parent2_name": "Read-only. The second parent’s name, for your eyes.",
        "parent2_type": "Optional. biological (default), adoptive, or step.",
        "marriage_ref": "Optional. Code of the marriage this person was born "
        "into, from the Marriages sheet.",
        "marriage_label": "Read-only. That couple’s names, for your eyes.",
        "system_id": "Do not edit. Lets a re-import update this exact person "
        "instead of adding a copy.",
    },
    "fa": {
        "ref": "اختیاری. کد کوتاه این ردیف (P1، P2…). فقط وقتی لازم است که "
        "ردیف دیگری به این‌جا اشاره کند.",
        "name": "اجباری. نام کوچک.",
        "family_name": "اختیاری.",
        "gender": "اجباری. مرد یا زن.",
        "birth_date": "اختیاری. اگر نمی‌دانید خالی بگذارید.",
        "death_date": "اختیاری. برای فرد زنده خالی بگذارید.",
        "birth_place": "اختیاری.",
        "death_place": "اختیاری.",
        "notes": "اختیاری. هر چیزی که می‌خواهید یادتان بماند.",
        "parent1_ref": "اختیاری. کد والد اول.",
        "parent1_name": "فقط‌خواندنی. نام والد اول، برای خواندن شما.",
        "parent1_type": "اختیاری. بیولوژیک (پیش‌فرض)، فرزندخواندگی یا ناتنی.",
        "parent2_ref": "اختیاری. کد والد دوم.",
        "parent2_name": "فقط‌خواندنی. نام والد دوم، برای خواندن شما.",
        "parent2_type": "اختیاری. بیولوژیک (پیش‌فرض)، فرزندخواندگی یا ناتنی.",
        "marriage_ref": "اختیاری. کد ازدواجی که این فرد از آن به دنیا آمده، از "
        "برگهٔ ازدواج‌ها.",
        "marriage_label": "فقط‌خواندنی. نام آن زوج، برای خواندن شما.",
        "system_id": "دست نزنید. باعث می‌شود ورود مجدد همین فرد را به‌روز کند، "
        "نه این‌که نسخهٔ تکراری بسازد.",
    },
}

_MARRIAGE_COLUMN_HELP: dict[str, dict[str, str]] = {
    "en": {
        "ref": "Optional. Short code for this marriage (M1, M2…). Needed if a "
        "child points at it.",
        "spouse_a_ref": "Required. Code of the first spouse.",
        "spouse_a_name": "Read-only. That spouse’s name, for your eyes.",
        "spouse_b_ref": "Required. Code of the second spouse.",
        "spouse_b_name": "Read-only. That spouse’s name, for your eyes.",
        "married_at": "Required.",
        "divorced_at": "Optional. Leave empty if still married.",
        "system_id": "Do not edit. Lets a re-import recognise this exact "
        "marriage.",
    },
    "fa": {
        "ref": "اختیاری. کد کوتاه این ازدواج (M1، M2…). اگر فرزندی به آن اشاره "
        "کند لازم است.",
        "spouse_a_ref": "اجباری. کد همسر اول.",
        "spouse_a_name": "فقط‌خواندنی. نام آن همسر، برای خواندن شما.",
        "spouse_b_ref": "اجباری. کد همسر دوم.",
        "spouse_b_name": "فقط‌خواندنی. نام آن همسر، برای خواندن شما.",
        "married_at": "اجباری.",
        "divorced_at": "اختیاری. اگر ازدواج برقرار است خالی بگذارید.",
        "system_id": "دست نزنید. باعث می‌شود ورود مجدد همین ازدواج را بشناسد.",
    },
}

_INSTRUCTION_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "sample_title": "Family tree — Excel template",
        "export_title": "Family tree — exported data",
        "how_to": "How to fill this in",
        "columns_persons": "Columns of the “{sheet}” sheet",
        "columns_marriages": "Columns of the “{sheet}” sheet",
        "column": "Column",
        "meaning": "What goes in it",
        "export_note": "This file was exported from your tree. Edit it and "
        "upload it again to add what is new — rows that are already in the "
        "tree are recognised and skipped.",
    },
    "fa": {
        "sample_title": "شجره‌نامه — قالب اکسل",
        "export_title": "شجره‌نامه — دادهٔ خروجی",
        "how_to": "چطور پر کنیم",
        "columns_persons": "ستون‌های برگهٔ «{sheet}»",
        "columns_marriages": "ستون‌های برگهٔ «{sheet}»",
        "column": "ستون",
        "meaning": "چه چیزی در آن می‌رود",
        "export_note": "این فایل از شجرهٔ شما خروجی گرفته شده است. آن را ویرایش "
        "کنید و دوباره بارگذاری کنید تا موارد جدید اضافه شوند — ردیف‌هایی که از "
        "قبل در شجره هستند شناسایی و رد می‌شوند.",
    },
}


def _write_band(ws, row: int, label: str) -> None:
    """A section heading that spans both columns, so the fill is not half-painted."""
    for column in (1, 2):
        cell = ws.cell(row=row, column=column, value=label if column == 1 else None)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL


def _write_instructions(ws, *, lang: str, title_key: str, note: str | None) -> None:
    text = ExcelText(lang)
    labels = _INSTRUCTION_LABELS[lang]
    ws.sheet_view.rightToLeft = lang == "fa"
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 88

    row = 1
    title_cell = ws.cell(row=row, column=1, value=labels[title_key])
    title_cell.font = TITLE_FONT
    row += 2

    if note:
        note_cell = ws.cell(row=row, column=1, value=note)
        note_cell.alignment = Alignment(wrap_text=True, vertical="top")
        row += 2

    _write_band(ws, row, labels["how_to"])
    row += 1
    for index, line in enumerate(_HOW_TO[lang], start=1):
        body = line.format(
            persons=text.persons_sheet,
            marriages=text.marriages_sheet,
            code=text.person_header("ref"),
            parent_code=text.person_header("parent1_ref"),
            parent_name=text.person_header("parent1_name"),
            marriage_code=text.person_header("marriage_ref"),
            hint=text.message("date_hint"),
        )
        ws.cell(row=row, column=1, value=str(index))
        cell = ws.cell(row=row, column=2, value=body)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        row += 1
    row += 1

    for sheet_label, columns, help_map, header_for in (
        (
            labels["columns_persons"].format(sheet=text.persons_sheet),
            PERSON_COLUMNS,
            _PERSON_COLUMN_HELP[lang],
            text.person_header,
        ),
        (
            labels["columns_marriages"].format(sheet=text.marriages_sheet),
            MARRIAGE_COLUMNS,
            _MARRIAGE_COLUMN_HELP[lang],
            text.marriage_header,
        ),
    ):
        _write_band(ws, row, sheet_label)
        row += 1
        head_a = ws.cell(row=row, column=1, value=labels["column"])
        head_b = ws.cell(row=row, column=2, value=labels["meaning"])
        for cell in (head_a, head_b):
            cell.font = LEGEND_KEY_FONT
            cell.border = THIN_BORDER
        row += 1
        for key in columns:
            name_cell = ws.cell(row=row, column=1, value=header_for(key))
            help_cell = ws.cell(row=row, column=2, value=help_map[key])
            name_cell.font = LEGEND_KEY_FONT
            name_cell.border = THIN_BORDER
            help_cell.border = THIN_BORDER
            help_cell.alignment = Alignment(wrap_text=True, vertical="top")
            row += 1
        row += 1


_SAMPLE_PEOPLE: list[dict[str, Any]] = [
    {
        "ref": "P1",
        "name": {"en": "Ali", "fa": "علی"},
        "family_name": {"en": "Karimi", "fa": "کریمی"},
        "gender": Gender.MALE,
        "birth_date": "1330/01/01",
        "birth_place": {"en": "Tehran", "fa": "تهران"},
        "notes": {"en": "Grandfather", "fa": "پدربزرگ"},
    },
    {
        "ref": "P2",
        "name": {"en": "Zahra", "fa": "زهرا"},
        "family_name": {"en": "Karimi", "fa": "کریمی"},
        "gender": Gender.FEMALE,
        "birth_date": "1335/05/10",
        "birth_place": {"en": "Tehran", "fa": "تهران"},
        "notes": {"en": "Grandmother", "fa": "مادربزرگ"},
    },
    {
        "ref": "P3",
        "name": {"en": "Reza", "fa": "رضا"},
        "family_name": {"en": "Karimi", "fa": "کریمی"},
        "gender": Gender.MALE,
        "birth_date": "1358/03/20",
        "birth_place": {"en": "Tehran", "fa": "تهران"},
        "notes": {"en": "Father", "fa": "پدر"},
        "parent1_ref": "P1",
        "parent2_ref": "P2",
        "marriage_ref": "M1",
    },
    {
        "ref": "P4",
        "name": {"en": "Sara", "fa": "سارا"},
        "family_name": {"en": "Ahmadi", "fa": "احمدی"},
        "gender": Gender.FEMALE,
        "birth_date": "1360/07/01",
        "birth_place": {"en": "Isfahan", "fa": "اصفهان"},
        "notes": {"en": "Mother", "fa": "مادر"},
    },
    {
        "ref": "P5",
        "name": {"en": "Arash", "fa": "آرش"},
        "family_name": {"en": "Karimi", "fa": "کریمی"},
        "gender": Gender.MALE,
        "birth_date": "1379/09/01",
        "birth_place": {"en": "Tehran", "fa": "تهران"},
        "notes": {"en": "Child", "fa": "فرزند"},
        "parent1_ref": "P3",
        "parent2_ref": "P4",
        "marriage_ref": "M2",
    },
]

_SAMPLE_MARRIAGES: list[dict[str, Any]] = [
    {
        "ref": "M1",
        "spouse_a_ref": "P1",
        "spouse_b_ref": "P2",
        "married_at": {"en": "1955-06-01", "fa": "1334/03/10"},
    },
    {
        "ref": "M2",
        "spouse_a_ref": "P3",
        "spouse_b_ref": "P4",
        "married_at": {"en": "1985-04-12", "fa": "1364/01/23"},
    },
]


def _localized(value: Any, lang: str) -> Any:
    return value.get(lang, "") if isinstance(value, dict) else value


def _sample_person_values(
    spec: dict[str, Any], names: dict[str, str], text: ExcelText
) -> list[Any]:
    lang = text.lang
    parent1 = spec.get("parent1_ref")
    parent2 = spec.get("parent2_ref")
    marriage_ref = spec.get("marriage_ref")
    couple = _sample_couple_label(marriage_ref, names) if marriage_ref else ""
    values: dict[str, Any] = {
        "ref": spec["ref"],
        "name": _localized(spec["name"], lang),
        "family_name": _localized(spec.get("family_name", ""), lang),
        "gender": text.gender_label(spec["gender"]),
        "birth_date": spec.get("birth_date", ""),
        "death_date": spec.get("death_date", ""),
        "birth_place": _localized(spec.get("birth_place", ""), lang),
        "death_place": _localized(spec.get("death_place", ""), lang),
        "notes": _localized(spec.get("notes", ""), lang),
        "parent1_ref": parent1 or "",
        "parent1_name": names.get(parent1, "") if parent1 else "",
        "parent1_type": (
            text.rel_type_label(ParentRelationshipType.BIOLOGICAL) if parent1 else ""
        ),
        "parent2_ref": parent2 or "",
        "parent2_name": names.get(parent2, "") if parent2 else "",
        "parent2_type": (
            text.rel_type_label(ParentRelationshipType.BIOLOGICAL) if parent2 else ""
        ),
        "marriage_ref": marriage_ref or "",
        "marriage_label": couple,
        "system_id": "",
    }
    return [values[key] for key in PERSON_COLUMNS]


def _sample_couple_label(marriage_ref: str, names: dict[str, str]) -> str:
    for marriage in _SAMPLE_MARRIAGES:
        if marriage["ref"] != marriage_ref:
            continue
        return _couple_label(
            names.get(marriage["spouse_a_ref"], ""),
            names.get(marriage["spouse_b_ref"], ""),
        )
    return ""


def _couple_label(name_a: str, name_b: str) -> str:
    parts = [part for part in (name_a, name_b) if part]
    return " × ".join(parts)


def build_sample_workbook(*, lang: str = "en") -> bytes:
    text = ExcelText(_normalize_locale(lang))
    locale = text.lang
    wb = Workbook()

    instructions = wb.active
    instructions.title = text.instructions_sheet
    _write_instructions(
        instructions, lang=locale, title_key="sample_title", note=None
    )

    names = {
        spec["ref"]: " ".join(
            part
            for part in (
                _localized(spec["name"], locale),
                _localized(spec.get("family_name", ""), locale),
            )
            if part
        )
        for spec in _SAMPLE_PEOPLE
    }

    persons = wb.create_sheet(text.persons_sheet)
    _style_header(persons, PERSON_COLUMNS, text.person_headers())
    _apply_sheet_view(persons, lang=locale)
    _add_person_validations(persons, lang=locale)
    _add_marriage_ref_validation(persons, text.marriages_sheet)
    for row_index, spec in enumerate(_SAMPLE_PEOPLE, start=2):
        for col_index, value in enumerate(
            _sample_person_values(spec, names, text), start=1
        ):
            cell = persons.cell(row=row_index, column=col_index, value=value)
            cell.fill = SAMPLE_FILL
    _shade_display_columns(
        persons,
        PERSON_COLUMNS,
        PERSON_DISPLAY_COLUMNS,
        last_row=len(_SAMPLE_PEOPLE) + 1,
    )

    marriages = wb.create_sheet(text.marriages_sheet)
    _style_header(marriages, MARRIAGE_COLUMNS, text.marriage_headers())
    _apply_sheet_view(marriages, lang=locale)
    _add_marriage_validations(marriages, text.persons_sheet)
    for row_index, spec in enumerate(_SAMPLE_MARRIAGES, start=2):
        values: dict[str, Any] = {
            "ref": spec["ref"],
            "spouse_a_ref": spec["spouse_a_ref"],
            "spouse_a_name": names.get(spec["spouse_a_ref"], ""),
            "spouse_b_ref": spec["spouse_b_ref"],
            "spouse_b_name": names.get(spec["spouse_b_ref"], ""),
            "married_at": _localized(spec["married_at"], locale),
            "divorced_at": "",
            "system_id": "",
        }
        for col_index, key in enumerate(MARRIAGE_COLUMNS, start=1):
            cell = marriages.cell(row=row_index, column=col_index, value=values[key])
            cell.fill = SAMPLE_FILL
    _shade_display_columns(
        marriages,
        MARRIAGE_COLUMNS,
        MARRIAGE_DISPLAY_COLUMNS,
        last_row=len(_SAMPLE_MARRIAGES) + 1,
    )

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def build_export_workbook(
    *,
    persons: list[Person],
    marriages: list[Marriage],
    lang: str = "en",
) -> bytes:
    text = ExcelText(_normalize_locale(lang))
    locale = text.lang
    wb = Workbook()
    instructions = wb.active
    instructions.title = text.instructions_sheet
    _write_instructions(
        instructions,
        lang=locale,
        title_key="export_title",
        note=_INSTRUCTION_LABELS[locale]["export_note"],
    )

    # Short readable codes for humans; the UUID lives in its own column so a
    # re-import can still recognise the exact person behind a row.
    person_code = {
        person.safe_id: f"P{index}" for index, person in enumerate(persons, start=1)
    }
    marriage_code = {
        marriage.safe_id: f"M{index}"
        for index, marriage in enumerate(marriages, start=1)
    }
    person_name = {
        person.safe_id: person_display_label(person, with_birth_date=False)
        for person in persons
    }
    marriage_couple = {
        marriage.safe_id: _couple_label(
            person_name.get(marriage.spouse_a_id, ""),
            person_name.get(marriage.spouse_b_id, ""),
        )
        for marriage in marriages
    }

    persons_ws = wb.create_sheet(text.persons_sheet)
    _style_header(persons_ws, PERSON_COLUMNS, text.person_headers())
    _apply_sheet_view(persons_ws, lang=locale)
    _add_person_validations(persons_ws, lang=locale)
    _add_marriage_ref_validation(persons_ws, text.marriages_sheet)

    for row_index, person in enumerate(persons, start=2):
        parents = list(person.parents)
        p1 = parents[0] if len(parents) > 0 else None
        p2 = parents[1] if len(parents) > 1 else None
        values: dict[str, Any] = {
            "ref": person_code[person.safe_id],
            "name": person.name,
            "family_name": person.family_name or "",
            "gender": text.gender_label(person.gender),
            "birth_date": format_excel_date(person.birth_date, lang=locale),
            "death_date": format_excel_date(person.death_date, lang=locale),
            "birth_place": person.birth_place or "",
            "death_place": person.death_place or "",
            "notes": person.notes or "",
            "parent1_ref": person_code.get(p1.parent_id, "") if p1 else "",
            "parent1_name": person_name.get(p1.parent_id, "") if p1 else "",
            "parent1_type": text.rel_type_label(p1.relationship_type) if p1 else "",
            "parent2_ref": person_code.get(p2.parent_id, "") if p2 else "",
            "parent2_name": person_name.get(p2.parent_id, "") if p2 else "",
            "parent2_type": text.rel_type_label(p2.relationship_type) if p2 else "",
            "marriage_ref": (
                marriage_code.get(person.marriage_id, "")
                if person.marriage_id
                else ""
            ),
            "marriage_label": (
                marriage_couple.get(person.marriage_id, "")
                if person.marriage_id
                else ""
            ),
            "system_id": str(person.safe_id),
        }
        for col_index, key in enumerate(PERSON_COLUMNS, start=1):
            persons_ws.cell(row=row_index, column=col_index, value=values[key])
    _shade_display_columns(
        persons_ws,
        PERSON_COLUMNS,
        PERSON_DISPLAY_COLUMNS,
        last_row=len(persons) + 1,
    )

    marriages_ws = wb.create_sheet(text.marriages_sheet)
    _style_header(marriages_ws, MARRIAGE_COLUMNS, text.marriage_headers())
    _apply_sheet_view(marriages_ws, lang=locale)
    _add_marriage_validations(marriages_ws, text.persons_sheet)
    for row_index, marriage in enumerate(marriages, start=2):
        values = {
            "ref": marriage_code[marriage.safe_id],
            "spouse_a_ref": person_code.get(
                marriage.spouse_a_id, str(marriage.spouse_a_id)
            ),
            "spouse_a_name": person_name.get(marriage.spouse_a_id, ""),
            "spouse_b_ref": person_code.get(
                marriage.spouse_b_id, str(marriage.spouse_b_id)
            ),
            "spouse_b_name": person_name.get(marriage.spouse_b_id, ""),
            "married_at": format_excel_date(marriage.married_at, lang=locale),
            "divorced_at": format_excel_date(marriage.divorced_at, lang=locale),
            "system_id": str(marriage.safe_id),
        }
        for col_index, key in enumerate(MARRIAGE_COLUMNS, start=1):
            marriages_ws.cell(row=row_index, column=col_index, value=values[key])
    _shade_display_columns(
        marriages_ws,
        MARRIAGE_COLUMNS,
        MARRIAGE_DISPLAY_COLUMNS,
        last_row=len(marriages) + 1,
    )

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def _resolve_sheet(wb, aliases: tuple[str, ...], *, label: str, text: ExcelText):
    by_key = {name.strip().casefold(): name for name in wb.sheetnames}
    for alias in aliases:
        found = by_key.get(alias.strip().casefold())
        if found is not None:
            return wb[found]
    raise TreeExcelInvalidException(
        detail=[text.message("missing_sheet", sheet=label)]
    )


def _header_map(ws, lookup: dict[str, str]) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for col in range(1, ws.max_column + 1):
        raw = ws.cell(row=1, column=col).value
        if raw is None:
            continue
        key = str(raw).strip().casefold()
        canonical = lookup.get(key, key)
        mapping.setdefault(canonical, col)
    return mapping


def _require_headers(
    mapping: dict[str, int],
    required: tuple[str, ...],
    *,
    sheet: str,
    labels: dict[str, str],
    text: ExcelText,
) -> None:
    missing = [labels[name] for name in required if name not in mapping]
    if not missing:
        return
    separator = "، " if text.lang == "fa" else ", "
    raise TreeExcelInvalidException(
        detail=[
            text.message(
                "missing_columns", sheet=sheet, columns=separator.join(missing)
            )
        ]
    )


def _parse_uuid_cell(value: Any) -> UUID | None:
    raw = _cell_str(value)
    return try_parse_excel_uuid(raw) if raw else None


def _auto_ref(prefix: str, row_number: int, taken: set[str]) -> str:
    candidate = f"{prefix}{row_number}"
    suffix = 1
    while candidate in taken:
        candidate = f"{prefix}{row_number}-{suffix}"
        suffix += 1
    return candidate


def parse_tree_excel(content: bytes, *, lang: str = "en") -> ParsedTreeExcel:
    """Read a workbook, reporting every bad cell instead of only the first."""
    text = excel_text(lang)
    try:
        wb = load_workbook(BytesIO(content), data_only=True)
    except (OSError, ValueError, KeyError) as exc:
        raise TreeExcelInvalidException(
            detail=[text.message("unreadable")]
        ) from exc

    persons_ws = _resolve_sheet(
        wb, PERSONS_SHEET_ALIASES, label=text.persons_sheet, text=text
    )
    marriages_ws = _resolve_sheet(
        wb, MARRIAGES_SHEET_ALIASES, label=text.marriages_sheet, text=text
    )
    person_cols = _header_map(persons_ws, _PERSON_HEADER_LOOKUP)
    marriage_cols = _header_map(marriages_ws, _MARRIAGE_HEADER_LOOKUP)

    _require_headers(
        person_cols,
        PERSON_REQUIRED_COLUMNS,
        sheet=text.persons_sheet,
        labels=_PERSON_HEADER_LABELS[text.lang],
        text=text,
    )
    _require_headers(
        marriage_cols,
        MARRIAGE_REQUIRED_COLUMNS,
        sheet=text.marriages_sheet,
        labels=_MARRIAGE_HEADER_LABELS[text.lang],
        text=text,
    )

    errors: list[str] = []
    persons = _parse_person_rows(persons_ws, person_cols, text, errors)
    marriages = _parse_marriage_rows(marriages_ws, marriage_cols, text, errors)
    return ParsedTreeExcel(persons=persons, marriages=marriages, errors=errors)


def _ref_index(ws, column: int | None) -> dict[str, int]:
    """First row claiming each code, read before any row is validated.

    Reading codes up front keeps duplicate detection independent of whether a
    row parses: a row skipped for a bad date must not silently free its code
    and turn one upload's clash into the next upload's surprise.
    """
    first_row: dict[str, int] = {}
    if column is None:
        return first_row
    for row in range(2, ws.max_row + 1):
        value = _cell_str(ws.cell(row=row, column=column).value)
        if value:
            first_row.setdefault(value, row)
    return first_row


def _parse_person_rows(
    ws, cols: dict[str, int], text: ExcelText, errors: list[str]
) -> list[ExcelPersonRow]:
    ref_rows = _ref_index(ws, cols.get("ref"))
    taken_refs = set(ref_rows)
    rows: list[ExcelPersonRow] = []

    for row_number in range(2, ws.max_row + 1):

        def get(name: str) -> Any:
            col = cols.get(name)
            if col is None:
                return None
            return ws.cell(row=row_number, column=col).value

        ref = _cell_str(get("ref"))
        name = _cell_str(get("name"))
        gender_raw = get("gender")
        if not ref and not name and not _cell_str(gender_raw):
            continue

        issues = _RowIssues()
        if not name:
            issues.add(
                text.persons_row(
                    row_number, "name_required", column=text.person_header("name")
                )
            )
        if ref and ref_rows[ref] != row_number:
            issues.add(
                text.persons_row(
                    row_number,
                    "duplicate_ref",
                    ref=ref,
                    other=ref_rows[ref],
                )
            )
            ref = None

        gender = _parse_gender_cell(
            gender_raw, issues=issues, text=text, row_number=row_number
        )
        birth_date = _parse_date_cell(
            get("birth_date"),
            column=text.person_header("birth_date"),
            issues=issues,
            text=text,
            row_number=row_number,
            sheet_row="persons_row",
        )
        death_date = _parse_date_cell(
            get("death_date"),
            column=text.person_header("death_date"),
            issues=issues,
            text=text,
            row_number=row_number,
            sheet_row="persons_row",
        )
        parent1_type = _parse_rel_type_cell(
            get("parent1_type"),
            column=text.person_header("parent1_type"),
            issues=issues,
            text=text,
            row_number=row_number,
        )
        parent2_type = _parse_rel_type_cell(
            get("parent2_type"),
            column=text.person_header("parent2_type"),
            issues=issues,
            text=text,
            row_number=row_number,
        )

        if issues or name is None or gender is None:
            errors.extend(issues.messages)
            continue

        if not ref:
            ref = _auto_ref("R", row_number, taken_refs)
            taken_refs.add(ref)

        rows.append(
            ExcelPersonRow(
                ref=ref,
                name=name,
                gender=gender,
                family_name=_cell_str(get("family_name")),
                birth_date=birth_date,
                death_date=death_date,
                birth_place=_cell_str(get("birth_place")),
                death_place=_cell_str(get("death_place")),
                notes=_cell_str(get("notes")),
                parent1_ref=_cell_str(get("parent1_ref")),
                parent1_type=parent1_type,
                parent2_ref=_cell_str(get("parent2_ref")),
                parent2_type=parent2_type,
                marriage_ref=_cell_str(get("marriage_ref")),
                system_id=_parse_uuid_cell(get("system_id")),
                row_number=row_number,
            )
        )

    return rows


def _parse_marriage_rows(
    ws, cols: dict[str, int], text: ExcelText, errors: list[str]
) -> list[ExcelMarriageRow]:
    ref_rows = _ref_index(ws, cols.get("ref"))
    taken_refs = set(ref_rows)
    rows: list[ExcelMarriageRow] = []

    for row_number in range(2, ws.max_row + 1):

        def get(name: str) -> Any:
            col = cols.get(name)
            if col is None:
                return None
            return ws.cell(row=row_number, column=col).value

        ref = _cell_str(get("ref"))
        spouse_a = _cell_str(get("spouse_a_ref"))
        spouse_b = _cell_str(get("spouse_b_ref"))
        married_raw = get("married_at")
        if not ref and not spouse_a and not spouse_b and not _cell_str(married_raw):
            continue

        issues = _RowIssues()
        if not spouse_a or not spouse_b:
            issues.add(
                text.marriages_row(
                    row_number,
                    "spouse_required",
                    column_a=text.marriage_header("spouse_a_ref"),
                    column_b=text.marriage_header("spouse_b_ref"),
                )
            )
        if ref and ref_rows[ref] != row_number:
            issues.add(
                text.marriages_row(
                    row_number, "duplicate_ref", ref=ref, other=ref_rows[ref]
                )
            )
            ref = None

        married_at = _parse_date_cell(
            married_raw,
            column=text.marriage_header("married_at"),
            issues=issues,
            text=text,
            row_number=row_number,
            sheet_row="marriages_row",
        )
        if married_at is None and _cell_str(married_raw) is None:
            issues.add(
                text.marriages_row(
                    row_number,
                    "married_at_required",
                    column=text.marriage_header("married_at"),
                )
            )
        divorced_at = _parse_date_cell(
            get("divorced_at"),
            column=text.marriage_header("divorced_at"),
            issues=issues,
            text=text,
            row_number=row_number,
            sheet_row="marriages_row",
        )

        if issues or married_at is None or not spouse_a or not spouse_b:
            errors.extend(issues.messages)
            continue

        if not ref:
            ref = _auto_ref("RM", row_number, taken_refs)
            taken_refs.add(ref)

        rows.append(
            ExcelMarriageRow(
                ref=ref,
                spouse_a_ref=spouse_a,
                spouse_b_ref=spouse_b,
                married_at=married_at,
                divorced_at=divorced_at,
                system_id=_parse_uuid_cell(get("system_id")),
                row_number=row_number,
            )
        )

    return rows


PersonIdentityKey = tuple[str, str, str, date | None]
MarriageFileKey = tuple[frozenset[str], date]
MarriageExistingKey = tuple[frozenset[UUID], date]


def person_identity_key(
    name: str,
    family_name: str | None,
    gender: Gender | str,
    birth_date: date | None,
) -> PersonIdentityKey:
    gender_value = gender.value if isinstance(gender, Gender) else str(gender)
    return (
        name.strip().casefold(),
        (family_name or "").strip().casefold(),
        gender_value.strip().lower(),
        birth_date,
    )


def person_display_label(person: Person, *, with_birth_date: bool = True) -> str:
    parts = [person.name]
    if person.family_name:
        parts.append(person.family_name)
    label = " ".join(parts)
    if with_birth_date and person.birth_date:
        return f"{label} ({person.birth_date.isoformat()})"
    return label


def person_namesake_warning(other_ref: str, *, lang: str = "en") -> str:
    return excel_text(lang).message("namesake", ref=other_ref)


def person_ambiguous_identity_warning(*, lang: str = "en") -> str:
    return excel_text(lang).message("ambiguous_identity")


def try_parse_excel_uuid(value: str) -> UUID | None:
    text = value.strip()
    if len(text) != 36:
        return None
    try:
        return UUID(text)
    except ValueError:
        return None


def canonical_excel_ref(ref: str, duplicate_of: dict[str, str]) -> str:
    seen: set[str] = set()
    current = ref
    while current in duplicate_of and current not in seen:
        seen.add(current)
        current = duplicate_of[current]
    return current


@dataclass
class TreeExcelMatch:
    person_existing_id: dict[str, UUID] = field(default_factory=dict)
    person_existing_label: dict[str, str] = field(default_factory=dict)
    # Kept for API compatibility; in-file person rows are never auto-merged.
    person_duplicate_of: dict[str, str] = field(default_factory=dict)
    person_namesake_of: dict[str, str] = field(default_factory=dict)
    person_ambiguous_identity: set[str] = field(default_factory=set)
    marriage_existing_id: dict[str, UUID] = field(default_factory=dict)
    marriage_duplicate_of: dict[str, str] = field(default_factory=dict)

    def person_already_in_tree(self, ref: str) -> bool:
        return ref in self.person_existing_id

    def marriage_already_in_tree(self, ref: str) -> bool:
        return ref in self.marriage_existing_id

    def person_warning(self, ref: str, *, lang: str = "en") -> str | None:
        if ref in self.person_ambiguous_identity:
            return person_ambiguous_identity_warning(lang=lang)
        namesake = self.person_namesake_of.get(ref)
        if namesake is not None:
            return person_namesake_warning(namesake, lang=lang)
        return None


def match_tree_excel(
    parsed: ParsedTreeExcel,
    existing_persons: list[Person],
    existing_marriages: list[Marriage],
) -> TreeExcelMatch:
    existing_by_id = {person.safe_id: person for person in existing_persons}
    existing_by_key: dict[PersonIdentityKey, list[Person]] = {}
    for person in existing_persons:
        key = person_identity_key(
            person.name, person.family_name, person.gender, person.birth_date
        )
        existing_by_key.setdefault(key, []).append(person)

    def consume_existing(person: Person) -> None:
        key = person_identity_key(
            person.name, person.family_name, person.gender, person.birth_date
        )
        bucket = existing_by_key.get(key)
        if not bucket:
            return
        remaining = [item for item in bucket if item.safe_id != person.safe_id]
        if remaining:
            existing_by_key[key] = remaining
        else:
            existing_by_key.pop(key, None)

    match = TreeExcelMatch()
    file_key_to_ref: dict[PersonIdentityKey, str] = {}
    for row in parsed.persons:
        key = person_identity_key(row.name, row.family_name, row.gender, row.birth_date)
        if key in file_key_to_ref:
            # Namesakes stay separate people; only surface a preview warning.
            match.person_namesake_of[row.ref] = file_key_to_ref[key]
        else:
            file_key_to_ref[key] = row.ref

        # The dedicated system-id column comes first; a UUID typed into the
        # code column is how older exports carried the same information.
        row_uuid = row.system_id or try_parse_excel_uuid(row.ref)
        if row_uuid is not None and row_uuid in existing_by_id:
            existing = existing_by_id[row_uuid]
            match.person_existing_id[row.ref] = existing.safe_id
            match.person_existing_label[row.ref] = person_display_label(existing)
            consume_existing(existing)
            continue

        candidates = existing_by_key.get(key, [])
        if len(candidates) == 1:
            existing = candidates[0]
            match.person_existing_id[row.ref] = existing.safe_id
            match.person_existing_label[row.ref] = person_display_label(existing)
            consume_existing(existing)
        elif len(candidates) > 1:
            match.person_ambiguous_identity.add(row.ref)

    existing_marriage_by_id = {
        marriage.safe_id: marriage for marriage in existing_marriages
    }
    existing_marriage_by_key: dict[MarriageExistingKey, Marriage] = {}
    for marriage in existing_marriages:
        marriage_key = (
            frozenset({marriage.spouse_a_id, marriage.spouse_b_id}),
            marriage.married_at,
        )
        existing_marriage_by_key.setdefault(marriage_key, marriage)

    file_marriage_key_to_ref: dict[MarriageFileKey, str] = {}
    for marriage_row in parsed.marriages:
        file_key = (
            frozenset({marriage_row.spouse_a_ref, marriage_row.spouse_b_ref}),
            marriage_row.married_at,
        )
        if file_key in file_marriage_key_to_ref:
            match.marriage_duplicate_of[marriage_row.ref] = file_marriage_key_to_ref[
                file_key
            ]
        else:
            file_marriage_key_to_ref[file_key] = marriage_row.ref

        marriage_uuid = marriage_row.system_id or try_parse_excel_uuid(
            marriage_row.ref
        )
        if marriage_uuid is not None and marriage_uuid in existing_marriage_by_id:
            match.marriage_existing_id[marriage_row.ref] = marriage_uuid
            continue

        id_a = match.person_existing_id.get(marriage_row.spouse_a_ref)
        id_b = match.person_existing_id.get(marriage_row.spouse_b_ref)
        if id_a is None:
            spouse_a_uuid = try_parse_excel_uuid(marriage_row.spouse_a_ref)
            if spouse_a_uuid is not None and spouse_a_uuid in existing_by_id:
                id_a = spouse_a_uuid
        if id_b is None:
            spouse_b_uuid = try_parse_excel_uuid(marriage_row.spouse_b_ref)
            if spouse_b_uuid is not None and spouse_b_uuid in existing_by_id:
                id_b = spouse_b_uuid
        if id_a is None or id_b is None:
            continue
        existing_marriage = existing_marriage_by_key.get(
            (frozenset({id_a, id_b}), marriage_row.married_at)
        )
        if existing_marriage is not None:
            match.marriage_existing_id[marriage_row.ref] = existing_marriage.safe_id

    return match
