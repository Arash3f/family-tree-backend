from datetime import date
from uuid import UUID

import strawberry

from app.presentation.graphql.types.common import (
    DateRangeInput,
    MarriageSortByEnum,
    PaginationInput,
    SortOrderEnum,
)


@strawberry.type
class MarriageType:
    id: UUID | None
    husband_id: UUID
    wife_id: UUID
    married_at: date
    divorced_at: date | None = None


@strawberry.type
class MarriagePage:
    items: list[MarriageType]
    total: int
    page: int
    page_size: int


@strawberry.input
class MarriageCreateInput:
    husband_id: UUID
    wife_id: UUID
    married_at: date


@strawberry.input
class MarriageUpdateDataInput:
    husband_id: UUID | None = None
    wife_id: UUID | None = None
    married_at: date | None = None
    divorced_at: date | None = None


@strawberry.input
class MarriageUpdateWhereInput:
    marriage_id: UUID


@strawberry.input
class MarriageUpdateInput:
    data: MarriageUpdateDataInput
    where: MarriageUpdateWhereInput


@strawberry.input
class DivorceInput:
    marriage_id: UUID
    divorced_at: date


@strawberry.input
class MarriageFilterInput:
    id: UUID | None = None
    husband_id: UUID | None = None
    wife_id: UUID | None = None
    married_at: DateRangeInput | None = None
    divorced_at: DateRangeInput | None = None


@strawberry.input
class MarriageListInput:
    pagination: PaginationInput | None = None
    filters: MarriageFilterInput | None = None
    sort_order: SortOrderEnum | None = None
    sort_by: MarriageSortByEnum | None = None


def marriage_from_mapping(data: dict) -> MarriageType:
    return MarriageType(
        id=data.get("id"),
        husband_id=data["husband_id"],
        wife_id=data["wife_id"],
        married_at=data["married_at"],
        divorced_at=data.get("divorced_at"),
    )
