from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID, uuid4

from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.tree_excel_loader import (
    load_all_tree_marriages,
    load_all_tree_persons,
)
from app.application.services.tree_excel_service import (
    ExcelMarriageRow,
    ExcelPersonRow,
    excel_text,
    match_tree_excel,
    parse_tree_excel,
    person_display_label,
)
from app.domain.entities.marriage import Marriage
from app.domain.entities.person import ParentLink, ParentRelationshipType, Person
from app.domain.exceptions.family_tree_exceptions import TreeExcelEmptyException
from app.domain.services.marriage_rules import MarriageRulesService
from app.utils.app_exception import AppException
from app.utils.error_codes import ERROR_MESSAGES


@dataclass
class PreviewPersonDTO:
    ref: str
    name: str
    family_name: str | None
    gender: str
    birth_date: str | None
    death_date: str | None
    parent1_ref: str | None
    parent2_ref: str | None
    marriage_ref: str | None
    row_number: int
    already_exists: bool = False
    existing_label: str | None = None
    duplicate_of_ref: str | None = None
    warning: str | None = None
    #: Who the codes above point at, so the preview reads without decoding refs.
    parent1_label: str | None = None
    parent2_label: str | None = None
    marriage_label: str | None = None


@dataclass
class PreviewMarriageDTO:
    ref: str
    spouse_a_ref: str
    spouse_b_ref: str
    married_at: str
    divorced_at: str | None
    row_number: int
    already_exists: bool = False
    duplicate_of_ref: str | None = None
    warning: str | None = None
    spouse_a_label: str | None = None
    spouse_b_label: str | None = None


@dataclass
class PreviewTreeExcelResultDTO:
    valid: bool
    persons: list[PreviewPersonDTO] = field(default_factory=list)
    marriages: list[PreviewMarriageDTO] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _date_iso(value: date | None) -> str | None:
    return value.isoformat() if value else None


def _exc_messages(exc: AppException, lang: str) -> list[str]:
    if exc.detail:
        return [str(item) for item in exc.detail if item]
    catalog = ERROR_MESSAGES.get(lang) or ERROR_MESSAGES["en"]
    message = catalog.get(exc.code) or ERROR_MESSAGES["en"].get(exc.code)
    return [message or str(exc.code)]


def _person_preview(row: ExcelPersonRow) -> PreviewPersonDTO:
    return PreviewPersonDTO(
        ref=row.ref,
        name=row.name,
        family_name=row.family_name,
        gender=row.gender.value,
        birth_date=_date_iso(row.birth_date),
        death_date=_date_iso(row.death_date),
        parent1_ref=row.parent1_ref,
        parent2_ref=row.parent2_ref,
        marriage_ref=row.marriage_ref,
        row_number=row.row_number,
    )


def _marriage_preview(row: ExcelMarriageRow) -> PreviewMarriageDTO:
    return PreviewMarriageDTO(
        ref=row.ref,
        spouse_a_ref=row.spouse_a_ref,
        spouse_b_ref=row.spouse_b_ref,
        married_at=row.married_at.isoformat(),
        divorced_at=_date_iso(row.divorced_at),
        row_number=row.row_number,
    )


class PreviewTreeExcelUseCase:
    """Parse and logically validate an Excel import without writing data."""

    def __init__(
        self,
        uow: UnitOfWork,
        marriage_rules_service: MarriageRulesService,
    ):
        self.uow = uow
        self.marriage_rules_service = marriage_rules_service

    async def execute(
        self, *, tree_id: UUID, content: bytes, lang: str = "en"
    ) -> PreviewTreeExcelResultDTO:
        text = excel_text(lang)
        errors: list[str] = []

        try:
            parsed = parse_tree_excel(content, lang=text.lang)
        except AppException as exc:
            return PreviewTreeExcelResultDTO(
                valid=False, errors=_exc_messages(exc, text.lang)
            )

        # Cell-level problems from the parser come first: they tell the user
        # exactly which cells to fix before anything else is worth reading.
        errors.extend(parsed.errors)

        persons_out = [_person_preview(row) for row in parsed.persons]
        marriages_out = [_marriage_preview(row) for row in parsed.marriages]

        if not parsed.persons and not parsed.marriages:
            # When every row was rejected, the cell errors already say why;
            # adding "nothing to import" on top only reads as contradiction.
            if not parsed.errors:
                errors.extend(_exc_messages(TreeExcelEmptyException(), text.lang))
            return PreviewTreeExcelResultDTO(
                valid=False,
                persons=persons_out,
                marriages=marriages_out,
                errors=_dedupe(errors),
            )

        async with self.uow:
            await self.uow.family_trees.get_or_raise(tree_id)
            existing_persons = await load_all_tree_persons(self.uow, tree_id)
            existing_marriages = await load_all_tree_marriages(self.uow, tree_id)

        match = match_tree_excel(parsed, existing_persons, existing_marriages)
        existing_person_by_id = {person.safe_id: person for person in existing_persons}

        for preview_person in persons_out:
            preview_person.already_exists = match.person_already_in_tree(
                preview_person.ref
            )
            preview_person.existing_label = match.person_existing_label.get(
                preview_person.ref
            )
            preview_person.duplicate_of_ref = match.person_duplicate_of.get(
                preview_person.ref
            )
            preview_person.warning = match.person_warning(
                preview_person.ref, lang=text.lang
            )

        for preview_marriage_item in marriages_out:
            preview_marriage_item.already_exists = match.marriage_already_in_tree(
                preview_marriage_item.ref
            )
            preview_marriage_item.duplicate_of_ref = match.marriage_duplicate_of.get(
                preview_marriage_item.ref
            )

        person_ids: dict[str, UUID] = {}
        person_by_ref: dict[str, Person] = {}
        for row in parsed.persons:
            existing_id = match.person_existing_id.get(row.ref)
            if existing_id is not None:
                existing = existing_person_by_id[existing_id]
                person_ids[row.ref] = existing_id
                person_by_ref[row.ref] = existing
                continue
            try:
                person_id = uuid4()
                person = Person(
                    id=person_id,
                    name=row.name,
                    gender=row.gender,
                    tree_id=tree_id,
                    birth_date=row.birth_date,
                    death_date=row.death_date,
                    family_name=row.family_name,
                    birth_place=row.birth_place,
                    death_place=row.death_place,
                    notes=row.notes,
                    parents=[],
                    marriage_id=None,
                    photo_object_key=None,
                )
                person_ids[row.ref] = person_id
                person_by_ref[row.ref] = person
            except AppException as exc:
                for message in _exc_messages(exc, text.lang):
                    errors.append(text.persons_row_detail(row.row_number, message))

        _label_rows(
            persons_out,
            marriages_out,
            parsed_persons=parsed.persons,
            parsed_marriages=parsed.marriages,
            person_by_ref=person_by_ref,
        )

        marriage_by_ref: dict[str, ExcelMarriageRow] = {}
        marriage_ids: dict[str, UUID] = {}

        for marriage_row in parsed.marriages:
            marriage_by_ref[marriage_row.ref] = marriage_row
            if match.marriage_already_in_tree(marriage_row.ref):
                marriage_ids[marriage_row.ref] = match.marriage_existing_id[
                    marriage_row.ref
                ]
                continue

            spouse_a = person_by_ref.get(marriage_row.spouse_a_ref)
            spouse_b = person_by_ref.get(marriage_row.spouse_b_ref)

            for column_key, spouse, ref in (
                ("spouse_a_ref", spouse_a, marriage_row.spouse_a_ref),
                ("spouse_b_ref", spouse_b, marriage_row.spouse_b_ref),
            ):
                if spouse is None:
                    errors.append(
                        text.marriages_row(
                            marriage_row.row_number,
                            "unknown_spouse",
                            column=text.marriage_header(column_key),
                            ref=ref,
                            sheet=text.persons_sheet,
                        )
                    )
            if spouse_a is None or spouse_b is None:
                continue

            try:
                self.marriage_rules_service.validate_marriage(
                    spouse_a=spouse_a,
                    spouse_b=spouse_b,
                    marriage_date=marriage_row.married_at,
                )
            except AppException as exc:
                for message in _exc_messages(exc, text.lang):
                    errors.append(
                        text.marriages_row_detail(marriage_row.row_number, message)
                    )

            marriage_id = uuid4()
            try:
                Marriage(
                    id=marriage_id,
                    tree_id=tree_id,
                    spouse_a_id=spouse_a.safe_id,
                    spouse_b_id=spouse_b.safe_id,
                    married_at=marriage_row.married_at,
                    divorced_at=marriage_row.divorced_at,
                )
                marriage_ids[marriage_row.ref] = marriage_id
            except AppException as exc:
                for message in _exc_messages(exc, text.lang):
                    errors.append(
                        text.marriages_row_detail(marriage_row.row_number, message)
                    )

        for row in parsed.persons:
            if match.person_already_in_tree(row.ref):
                continue
            target_person = person_by_ref.get(row.ref)
            if target_person is None:
                continue

            parents: list[ParentLink] = []
            for column_key, parent_ref, rel_type in (
                ("parent1_ref", row.parent1_ref, row.parent1_type),
                ("parent2_ref", row.parent2_ref, row.parent2_type),
            ):
                if not parent_ref:
                    continue
                parent_id = person_ids.get(parent_ref)
                if parent_id is None:
                    errors.append(
                        text.persons_row(
                            row.row_number,
                            "unknown_parent",
                            column=text.person_header(column_key),
                            ref=parent_ref,
                            sheet=text.persons_sheet,
                        )
                    )
                    continue
                parents.append(
                    ParentLink(parent_id=parent_id, relationship_type=rel_type)
                )

            linked_marriage_id: UUID | None = None
            linked_marriage_row: ExcelMarriageRow | None = None
            if row.marriage_ref:
                linked_marriage_row = marriage_by_ref.get(row.marriage_ref)
                linked_marriage_id = marriage_ids.get(row.marriage_ref)
                if linked_marriage_row is None or linked_marriage_id is None:
                    errors.append(
                        text.persons_row(
                            row.row_number,
                            "unknown_marriage",
                            column=text.person_header("marriage_ref"),
                            ref=row.marriage_ref,
                            sheet=text.marriages_sheet,
                        )
                    )

            if not parents and linked_marriage_id is None:
                continue

            try:
                target_person.set_parents(parents)
                target_person.marriage_id = linked_marriage_id
            except AppException as exc:
                for message in _exc_messages(exc, text.lang):
                    errors.append(text.persons_row_detail(row.row_number, message))
                continue

            if linked_marriage_row is not None:
                spouse_refs = {
                    linked_marriage_row.spouse_a_ref,
                    linked_marriage_row.spouse_b_ref,
                }
                spouse_ids = {
                    person_ids[ref] for ref in spouse_refs if ref in person_ids
                }
                for link in target_person.parents:
                    if (
                        link.relationship_type is ParentRelationshipType.BIOLOGICAL
                        and link.parent_id not in spouse_ids
                    ):
                        errors.append(
                            text.persons_row(
                                row.row_number,
                                "bio_parents_marriage",
                                column=text.person_header("marriage_ref"),
                            )
                        )
                        break

            try:
                target_person.validate()
            except AppException as exc:
                for message in _exc_messages(exc, text.lang):
                    errors.append(text.persons_row_detail(row.row_number, message))

        unique_errors = _dedupe(errors)
        return PreviewTreeExcelResultDTO(
            valid=len(unique_errors) == 0,
            persons=persons_out,
            marriages=marriages_out,
            errors=unique_errors,
        )


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique


def _label_rows(
    persons_out: list[PreviewPersonDTO],
    marriages_out: list[PreviewMarriageDTO],
    *,
    parsed_persons: list[ExcelPersonRow],
    parsed_marriages: list[ExcelMarriageRow],
    person_by_ref: dict[str, Person],
) -> None:
    """Resolve every code shown in the preview to the name behind it."""
    file_labels = {row.ref: row.label for row in parsed_persons}

    def person_label(ref: str | None) -> str | None:
        if not ref:
            return None
        label = file_labels.get(ref)
        if label:
            return label
        existing = person_by_ref.get(ref)
        return (
            person_display_label(existing, with_birth_date=False)
            if existing is not None
            else None
        )

    couple_labels: dict[str, str] = {}
    for marriage in parsed_marriages:
        names = [
            name
            for name in (
                person_label(marriage.spouse_a_ref),
                person_label(marriage.spouse_b_ref),
            )
            if name
        ]
        if names:
            couple_labels[marriage.ref] = " × ".join(names)

    for person in persons_out:
        person.parent1_label = person_label(person.parent1_ref)
        person.parent2_label = person_label(person.parent2_ref)
        person.marriage_label = (
            couple_labels.get(person.marriage_ref) if person.marriage_ref else None
        )

    for marriage_dto in marriages_out:
        marriage_dto.spouse_a_label = person_label(marriage_dto.spouse_a_ref)
        marriage_dto.spouse_b_label = person_label(marriage_dto.spouse_b_ref)
