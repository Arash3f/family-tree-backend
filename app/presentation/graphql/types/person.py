from uuid import UUID

import strawberry

from app.presentation.graphql.types.common import (
    GenderEnum,
    JalaliDateRangeInput,
    PaginationInput,
    PersonSortByEnum,
    SortOrderEnum,
    format_jalali_date,
)


@strawberry.type
class PersonType:
    id: UUID | None
    name: str
    gender: GenderEnum
    birth_date: str | None = None
    death_date: str | None = None
    father_id: UUID | None = None
    mother_id: UUID | None = None


@strawberry.type
class PersonPage:
    items: list[PersonType]
    total: int
    page: int
    page_size: int


@strawberry.type
class ClosestRelationshipType:
    from_person_id: UUID
    to_person_id: UUID
    found: bool
    distance: int | None = None
    path_person_ids: list[UUID]
    relationship_types: list[str]


@strawberry.input
class PersonCreateInput:
    name: str
    gender: GenderEnum
    birth_date: str | None = None
    death_date: str | None = None
    father_id: UUID | None = None
    mother_id: UUID | None = None


@strawberry.input
class PersonUpdateDataInput:
    name: str | None = None
    gender: GenderEnum | None = None
    birth_date: str | None = None
    death_date: str | None = None
    father_id: UUID | None = None
    mother_id: UUID | None = None


@strawberry.input
class PersonUpdateWhereInput:
    person_id: UUID


@strawberry.input
class PersonUpdateInput:
    data: PersonUpdateDataInput
    where: PersonUpdateWhereInput


@strawberry.input
class PersonFilterInput:
    id: UUID | None = None
    name: str | None = None
    gender: GenderEnum | None = None
    birth_date: JalaliDateRangeInput | None = None
    father_id: UUID | None = None
    mother_id: UUID | None = None


@strawberry.input
class PersonListInput:
    pagination: PaginationInput | None = None
    filters: PersonFilterInput | None = None
    sort_order: SortOrderEnum | None = None
    sort_by: PersonSortByEnum | None = None


def person_from_mapping(data: dict) -> PersonType:
    gender = data["gender"]
    if hasattr(gender, "value"):
        gender_enum = GenderEnum(gender.value)
    else:
        gender_enum = GenderEnum(gender)

    birth = data.get("birth_date")
    death = data.get("death_date")
    if birth is not None and not isinstance(birth, str):
        birth = format_jalali_date(birth)
    if death is not None and not isinstance(death, str):
        death = format_jalali_date(death)

    return PersonType(
        id=data.get("id"),
        name=data["name"],
        gender=gender_enum,
        birth_date=birth,
        death_date=death,
        father_id=data.get("father_id"),
        mother_id=data.get("mother_id"),
    )
