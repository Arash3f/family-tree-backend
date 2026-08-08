from uuid import UUID

import strawberry

from app.presentation.graphql.types.common import (
    PaginationInput,
    PermissionSortByEnum,
    SortOrderEnum,
)


@strawberry.type
class PermissionType:
    id: UUID
    name: str


@strawberry.type
class PermissionPage:
    items: list[PermissionType]
    total: int
    page: int
    page_size: int


@strawberry.input
class PermissionFilterInput:
    id: UUID | None = None
    name: str | None = None


@strawberry.input
class PermissionListInput:
    pagination: PaginationInput | None = None
    filters: PermissionFilterInput | None = None
    sort_order: SortOrderEnum | None = None
    sort_by: PermissionSortByEnum | None = None


def permission_from_mapping(data: dict) -> PermissionType:
    return PermissionType(id=data["id"], name=data["name"])
