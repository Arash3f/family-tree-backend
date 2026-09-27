from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.application.dto.person.person_create_dto import ParentLinkDTO
from app.application.dto.person.person_get_dto import (
    PersonGetMapper,
    PersonGetResponseDTO,
)
from app.domain.entities.marriage import Marriage
from app.domain.entities.person import Gender, ParentRelationshipType, Person


class PersonCardSummaryDTO(BaseModel):
    """Compact person fields for parents, spouses, and descendant lists."""

    id: UUID
    name: str
    gender: Gender
    family_name: str | None = None
    birth_date: date | None = None
    death_date: date | None = None
    photo_url: str | None = None


class PersonCardParentDTO(BaseModel):
    parent_id: UUID
    relationship_type: ParentRelationshipType
    person: PersonCardSummaryDTO | None = None


class PersonCardMarriageDTO(BaseModel):
    id: UUID
    spouse_a_id: UUID
    spouse_b_id: UUID
    married_at: date | None = None
    divorced_at: date | None = None
    spouse: PersonCardSummaryDTO | None = None


class GenderCountsDTO(BaseModel):
    male: int = 0
    female: int = 0
    total: int = 0


class GenerationStatsDTO(BaseModel):
    generation: int
    male: int = 0
    female: int = 0
    total: int = 0
    people: list[PersonCardSummaryDTO] = Field(default_factory=list)


class DescendantStatsDTO(BaseModel):
    generations: list[GenerationStatsDTO] = Field(default_factory=list)
    total: GenderCountsDTO = Field(default_factory=GenderCountsDTO)


class PersonCardResponseDTO(BaseModel):
    person: PersonGetResponseDTO
    parents: list[PersonCardParentDTO] = Field(default_factory=list)
    marriages: list[PersonCardMarriageDTO] = Field(default_factory=list)
    descendants: DescendantStatsDTO = Field(default_factory=DescendantStatsDTO)


def person_summary(
    person: Person, photo_url: str | None = None
) -> PersonCardSummaryDTO:
    return PersonCardSummaryDTO(
        id=person.safe_id,
        name=person.name,
        gender=person.gender,
        family_name=person.family_name,
        birth_date=person.birth_date,
        death_date=person.death_date,
        photo_url=photo_url,
    )


def _empty_counts() -> GenderCountsDTO:
    return GenderCountsDTO()


def _add_person(counts: GenderCountsDTO, person: Person) -> None:
    counts.total += 1
    if person.gender == Gender.MALE:
        counts.male += 1
    elif person.gender == Gender.FEMALE:
        counts.female += 1


def _sort_people(
    people: list[Person],
) -> list[Person]:
    def key(person: Person):
        birth = person.birth_date
        return (
            birth is None,
            birth.year if birth else 0,
            birth.month if birth else 0,
            birth.day if birth else 0,
            person.name,
        )

    return sorted(people, key=key)


def count_descendants_by_generation(
    root_id: UUID,
    persons: list[Person],
    photo_url_of,
) -> DescendantStatsDTO:
    """Count unique descendants by closest generation (1 = children)."""
    by_id = {person.safe_id: person for person in persons}
    children_map: dict[UUID, list[Person]] = {}
    for person in persons:
        for link in person.parents:
            children_map.setdefault(link.parent_id, []).append(person)

    generation_of: dict[UUID, int] = {root_id: 0}
    queue = [root_id]
    while queue:
        current = queue.pop(0)
        gen = generation_of[current]
        for child in children_map.get(current, []):
            child_id = child.safe_id
            next_gen = gen + 1
            existing = generation_of.get(child_id)
            if existing is None or next_gen < existing:
                generation_of[child_id] = next_gen
                queue.append(child_id)

    by_gen: dict[int, GenderCountsDTO] = {}
    people_by_gen: dict[int, list[Person]] = {}
    total = _empty_counts()

    for person_id, generation in generation_of.items():
        if generation <= 0:
            continue
        person = by_id.get(person_id)
        if person is None:
            continue
        bucket = by_gen.setdefault(generation, _empty_counts())
        _add_person(bucket, person)
        _add_person(total, person)
        people_by_gen.setdefault(generation, []).append(person)

    generations = [
        GenerationStatsDTO(
            generation=generation,
            male=counts.male,
            female=counts.female,
            total=counts.total,
            people=[
                person_summary(person, photo_url_of(person))
                for person in _sort_people(people_by_gen.get(generation, []))
            ],
        )
        for generation, counts in sorted(by_gen.items())
    ]
    return DescendantStatsDTO(generations=generations, total=total)


def build_person_card(
    person: Person,
    *,
    tree_people: list[Person],
    marriages: list[Marriage],
    photo_url_of,
) -> PersonCardResponseDTO:
    by_id = {item.safe_id: item for item in tree_people}
    photo_url = photo_url_of(person)

    parents: list[PersonCardParentDTO] = []
    for link in person.parents:
        parent = by_id.get(link.parent_id)
        parents.append(
            PersonCardParentDTO(
                parent_id=link.parent_id,
                relationship_type=link.relationship_type,
                person=(
                    person_summary(parent, photo_url_of(parent)) if parent else None
                ),
            )
        )

    marriage_rows: list[PersonCardMarriageDTO] = []
    for marriage in marriages:
        other_id = (
            marriage.spouse_b_id
            if marriage.spouse_a_id == person.safe_id
            else marriage.spouse_a_id
        )
        spouse = by_id.get(other_id)
        marriage_rows.append(
            PersonCardMarriageDTO(
                id=marriage.safe_id,
                spouse_a_id=marriage.spouse_a_id,
                spouse_b_id=marriage.spouse_b_id,
                married_at=marriage.married_at,
                divorced_at=marriage.divorced_at,
                spouse=(
                    person_summary(spouse, photo_url_of(spouse)) if spouse else None
                ),
            )
        )

    return PersonCardResponseDTO(
        person=PersonGetMapper.to_response(person=person, photo_url=photo_url),
        parents=parents,
        marriages=marriage_rows,
        descendants=count_descendants_by_generation(
            person.safe_id, tree_people, photo_url_of
        ),
    )


# Re-export for mappers that need ParentLinkDTO typing nearby.
__all__ = [
    "PersonCardResponseDTO",
    "PersonCardSummaryDTO",
    "PersonCardParentDTO",
    "PersonCardMarriageDTO",
    "DescendantStatsDTO",
    "GenerationStatsDTO",
    "GenderCountsDTO",
    "build_person_card",
    "ParentLinkDTO",
]
