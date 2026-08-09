from enum import Enum
from uuid import UUID

import strawberry

from app.domain.entities.person import ParentRelationshipType
from app.presentation.graphql.types.common import (
    GenderEnum,
    JalaliDateRangeInput,
    PaginationInput,
    PersonSortByEnum,
    SortOrderEnum,
    format_jalali_date,
)


@strawberry.enum(name="ParentRelationshipType")
class ParentRelationshipTypeEnum(Enum):
    BIOLOGICAL = "biological"
    ADOPTIVE = "adoptive"
    STEP = "step"


def to_domain_relationship_type(
    value: ParentRelationshipTypeEnum | ParentRelationshipType,
) -> ParentRelationshipType:
    if isinstance(value, ParentRelationshipType):
        return value
    return ParentRelationshipType(value.value)


@strawberry.type
class ParentLinkType:
    parent_id: UUID
    relationship_type: ParentRelationshipTypeEnum


@strawberry.type
class PersonType:
    id: UUID | None
    name: str
    gender: GenderEnum
    birth_date: str | None = None
    death_date: str | None = None
    family_name: str | None = None
    birth_place: str | None = None
    death_place: str | None = None
    notes: str | None = None
    parents: list[ParentLinkType]
    marriage_id: UUID | None = None
    photo_object_key: str | None = None
    photo_url: str | None = None


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
class ParentLinkInput:
    parent_id: UUID
    relationship_type: ParentRelationshipTypeEnum = (
        ParentRelationshipTypeEnum.BIOLOGICAL
    )


@strawberry.input
class PersonCreateInput:
    name: str
    gender: GenderEnum
    birth_date: str | None = None
    death_date: str | None = None
    family_name: str | None = None
    birth_place: str | None = None
    death_place: str | None = None
    notes: str | None = None
    parents: list[ParentLinkInput] | None = None
    marriage_id: UUID | None = None
    photo_object_key: str | None = None


@strawberry.input
class PersonUpdateDataInput:
    name: str | None = None
    gender: GenderEnum | None = None
    birth_date: str | None = None
    death_date: str | None = None
    family_name: str | None = strawberry.UNSET
    birth_place: str | None = strawberry.UNSET
    death_place: str | None = strawberry.UNSET
    notes: str | None = strawberry.UNSET
    parents: list[ParentLinkInput] | None = strawberry.UNSET
    marriage_id: UUID | None = strawberry.UNSET
    photo_object_key: str | None = strawberry.UNSET


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
    parent_id: UUID | None = None
    relationship_type: ParentRelationshipTypeEnum | None = None
    marriage_id: UUID | None = None


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

    parents_raw = data.get("parents") or []
    parents: list[ParentLinkType] = []
    for link in parents_raw:
        if isinstance(link, dict):
            rel = link.get("relationship_type", "biological")
            if hasattr(rel, "value"):
                rel = rel.value
            parents.append(
                ParentLinkType(
                    parent_id=link["parent_id"],
                    relationship_type=ParentRelationshipTypeEnum(rel),
                )
            )
        else:
            rel = link.relationship_type
            if hasattr(rel, "value"):
                rel = rel.value
            parents.append(
                ParentLinkType(
                    parent_id=link.parent_id,
                    relationship_type=ParentRelationshipTypeEnum(rel),
                )
            )

    return PersonType(
        id=data.get("id"),
        name=data["name"],
        gender=gender_enum,
        birth_date=birth,
        death_date=death,
        family_name=data.get("family_name"),
        birth_place=data.get("birth_place"),
        death_place=data.get("death_place"),
        notes=data.get("notes"),
        parents=parents,
        marriage_id=data.get("marriage_id"),
        photo_object_key=data.get("photo_object_key"),
        photo_url=data.get("photo_url"),
    )
