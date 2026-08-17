from dataclasses import dataclass
from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.account_limit_service import AccountLimitService
from app.application.services.family_tree_sync_service import FamilyTreeSyncService
from app.application.services.tree_excel_loader import (
    load_all_tree_marriages,
    load_all_tree_persons,
)
from app.application.services.tree_excel_service import (
    canonical_excel_ref,
    match_tree_excel,
    parse_tree_excel,
)
from app.domain.entities.marriage import Marriage
from app.domain.entities.person import ParentLink, ParentRelationshipType, Person
from app.domain.exceptions.family_tree_exceptions import (
    TreeExcelEmptyException,
    TreeExcelInvalidException,
)
from app.domain.exceptions.person_exceptions import InvalidParentMarriageException
from app.domain.services.marriage_rules import MarriageRulesService


@dataclass
class ImportTreeExcelResultDTO:
    persons_created: int
    marriages_created: int


class ImportTreeExcelUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        marriage_rules_service: MarriageRulesService,
        sync_service: FamilyTreeSyncService | None = None,
        account_limit_service: AccountLimitService | None = None,
    ):
        self.uow = uow
        self.marriage_rules_service = marriage_rules_service
        self.sync_service = sync_service or FamilyTreeSyncService()
        self.account_limit_service = account_limit_service or AccountLimitService()

    async def execute(
        self,
        *,
        tree_id: UUID,
        content: bytes,
        person_refs: set[str] | None = None,
        marriage_refs: set[str] | None = None,
    ) -> ImportTreeExcelResultDTO:
        parsed = parse_tree_excel(content)
        if not parsed.persons and not parsed.marriages:
            raise TreeExcelEmptyException()

        person_ref_to_id: dict[str, UUID] = {}
        marriage_ref_to_id: dict[str, UUID] = {}
        created_persons: list[Person] = []
        created_marriages: list[Marriage] = []

        async with self.uow:
            await self.uow.family_trees.get_or_raise(tree_id)
            existing_persons = await load_all_tree_persons(self.uow, tree_id)
            existing_marriages = await load_all_tree_marriages(self.uow, tree_id)
            match = match_tree_excel(parsed, existing_persons, existing_marriages)

            selected_people = _normalize_selected_refs(
                person_refs, match.person_duplicate_of
            )
            selected_marriages = _normalize_selected_refs(
                marriage_refs, match.marriage_duplicate_of
            )

            persons_to_create = [
                row
                for row in parsed.persons
                if _should_create(
                    row.ref,
                    already_exists=match.person_already_in_tree(row.ref),
                    duplicate_of=match.person_duplicate_of,
                    selected=selected_people,
                )
            ]
            marriages_to_create = [
                row
                for row in parsed.marriages
                if _should_create(
                    row.ref,
                    already_exists=match.marriage_already_in_tree(row.ref),
                    duplicate_of=match.marriage_duplicate_of,
                    selected=selected_marriages,
                )
            ]
            await self.account_limit_service.assert_can_create_persons(
                self.uow, tree_id=tree_id, additional=len(persons_to_create)
            )
            await self.account_limit_service.assert_can_create_marriages(
                self.uow, tree_id=tree_id, additional=len(marriages_to_create)
            )

            person_ref_to_id.update(match.person_existing_id)
            marriage_ref_to_id.update(match.marriage_existing_id)

            for row in persons_to_create:
                person = Person(
                    id=None,
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
                person = await self.uow.persons.create(person)
                person_ref_to_id[row.ref] = person.safe_id
                created_persons.append(person)

            _fill_duplicate_refs(person_ref_to_id, match.person_duplicate_of)

            for marriage_row in marriages_to_create:
                spouse_a_id = person_ref_to_id.get(marriage_row.spouse_a_ref)
                spouse_b_id = person_ref_to_id.get(marriage_row.spouse_b_ref)
                if spouse_a_id is None or spouse_b_id is None:
                    raise TreeExcelInvalidException(
                        detail=[
                            f"Marriages row {marriage_row.row_number}: unknown "
                            f"spouse ref ('{marriage_row.spouse_a_ref}' / "
                            f"'{marriage_row.spouse_b_ref}'). Select those people "
                            "or make sure they already exist."
                        ]
                    )

                spouse_a = await self.uow.persons.get_in_tree_or_raise(
                    person_id=spouse_a_id, tree_id=tree_id
                )
                spouse_b = await self.uow.persons.get_in_tree_or_raise(
                    person_id=spouse_b_id, tree_id=tree_id
                )
                self.marriage_rules_service.validate_marriage(
                    spouse_a=spouse_a,
                    spouse_b=spouse_b,
                    marriage_date=marriage_row.married_at,
                )

                marriage = Marriage(
                    id=None,
                    tree_id=tree_id,
                    spouse_a_id=spouse_a_id,
                    spouse_b_id=spouse_b_id,
                    married_at=marriage_row.married_at,
                    divorced_at=marriage_row.divorced_at,
                )
                marriage = await self.uow.marriages.create(marriage)
                marriage_ref_to_id[marriage_row.ref] = marriage.safe_id
                created_marriages.append(marriage)

            _fill_duplicate_refs(marriage_ref_to_id, match.marriage_duplicate_of)

            created_ids = {person.safe_id for person in created_persons}
            for row in parsed.persons:
                person_id = person_ref_to_id.get(row.ref)
                if person_id is None or person_id not in created_ids:
                    continue
                person = await self.uow.persons.get_in_tree_or_raise(
                    person_id=person_id, tree_id=tree_id
                )

                parents: list[ParentLink] = []
                for parent_ref, rel_type in (
                    (row.parent1_ref, row.parent1_type),
                    (row.parent2_ref, row.parent2_type),
                ):
                    if not parent_ref:
                        continue
                    parent_id = person_ref_to_id.get(parent_ref)
                    if parent_id is None:
                        raise TreeExcelInvalidException(
                            detail=[
                                f"Persons row {row.row_number}: unknown parent ref "
                                f"'{parent_ref}'. Select that person or make sure "
                                "they already exist."
                            ]
                        )
                    parents.append(
                        ParentLink(parent_id=parent_id, relationship_type=rel_type)
                    )

                marriage_id = None
                if row.marriage_ref:
                    marriage_id = marriage_ref_to_id.get(row.marriage_ref)
                    if marriage_id is None:
                        raise TreeExcelInvalidException(
                            detail=[
                                f"Persons row {row.row_number}: unknown marriage_ref "
                                f"'{row.marriage_ref}'. Select that marriage or make "
                                "sure it already exists."
                            ]
                        )

                if not parents and marriage_id is None:
                    continue

                person.set_parents(parents)
                person.marriage_id = marriage_id

                if person.marriage_id is not None:
                    marriage = await self.uow.marriages.get_in_tree_or_raise(
                        marriage_id=person.marriage_id, tree_id=tree_id
                    )
                    spouse_ids = {marriage.spouse_a_id, marriage.spouse_b_id}
                    for link in person.parents:
                        if (
                            link.relationship_type is ParentRelationshipType.BIOLOGICAL
                            and link.parent_id not in spouse_ids
                        ):
                            raise InvalidParentMarriageException(
                                detail=[
                                    f"Persons row {row.row_number}: biological parents "
                                    "must match marriage_ref spouses"
                                ]
                            )

                person.validate()
                updated = await self.uow.persons.update(person=person)
                for index, created in enumerate(created_persons):
                    if created.safe_id == updated.safe_id:
                        created_persons[index] = updated
                        break

            if not created_persons and not created_marriages:
                raise TreeExcelEmptyException()

            await self.uow.commit()

        for person in created_persons:
            self.sync_service.upsert_person(person)
        for marriage in created_marriages:
            if marriage.is_active():
                self.sync_service.upsert_spouse(
                    marriage.spouse_a_id, marriage.spouse_b_id
                )

        return ImportTreeExcelResultDTO(
            persons_created=len(created_persons),
            marriages_created=len(created_marriages),
        )


def _normalize_selected_refs(
    selected: set[str] | None, duplicate_of: dict[str, str]
) -> set[str] | None:
    if selected is None:
        return None
    return {canonical_excel_ref(ref, duplicate_of) for ref in selected}


def _should_create(
    ref: str,
    *,
    already_exists: bool,
    duplicate_of: dict[str, str],
    selected: set[str] | None,
) -> bool:
    if already_exists or ref in duplicate_of:
        return False
    if selected is not None and ref not in selected:
        return False
    return True


def _fill_duplicate_refs(
    ref_to_id: dict[str, UUID], duplicate_of: dict[str, str]
) -> None:
    for ref, source in duplicate_of.items():
        if ref in ref_to_id:
            continue
        canonical = canonical_excel_ref(ref, duplicate_of)
        mapped = ref_to_id.get(canonical) or ref_to_id.get(source)
        if mapped is not None:
            ref_to_id[ref] = mapped
