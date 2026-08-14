from uuid import UUID

import strawberry

from app.presentation.graphql.types.common import (
    PaginationInput,
    RoleSortByEnum,
    SortOrderEnum,
)


@strawberry.type
class RoleType:
    id: UUID
    name: str
    permission_ids: list[UUID]
    user_count: int = 0


@strawberry.type
class RolePage:
    items: list[RoleType]
    total: int
    page: int
    page_size: int


@strawberry.input
class RoleCreateInput:
    name: str | None = None
    permission_ids: list[UUID] | None = None


@strawberry.input
class RoleUpdateDataInput:
    name: str | None = None
    permission_ids: list[UUID] | None = None


@strawberry.input
class RoleUpdateWhereInput:
    role_id: UUID


@strawberry.input
class RoleUpdateInput:
    data: RoleUpdateDataInput
    where: RoleUpdateWhereInput


@strawberry.input
class RoleFilterInput:
    id: UUID | None = None
    name: str | None = None
    permission_id: UUID | None = None


@strawberry.input
class RoleListInput:
    pagination: PaginationInput | None = None
    filters: RoleFilterInput | None = None
    sort_order: SortOrderEnum | None = None
    sort_by: RoleSortByEnum | None = None


def role_from_mapping(data: dict) -> RoleType:
    return RoleType(
        id=data["id"],
        name=data["name"],
        permission_ids=list(data.get("permission_ids") or []),
        user_count=int(data.get("user_count") or 0),
    )
