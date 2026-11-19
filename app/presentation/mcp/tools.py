"""MCP tool implementations — thin wrappers over existing use cases."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from app.application.services.person_photo_service import PersonPhotoService
from app.application.services.tree_access_service import TreeAccessService
from app.application.use_cases.family_tree.get_family_tree_use_case import (
    ListFamilyTreesUseCase,
)
from app.application.use_cases.person.get_closest_relationship_use_case import (
    GetClosestRelationshipUseCase,
)
from app.application.use_cases.person.get_person_card_use_case import (
    GetPersonCardUseCase,
)
from app.application.use_cases.person.get_person_list_by_filter_use_case import (
    GetPersonListByFilterUseCase,
)
from app.application.use_cases.person.get_person_use_case import GetPersonUseCase
from app.domain.shared.dto.common_dto import IdDTO
from app.domain.shared.dto.pagination_dto import PaginationParams
from app.domain.shared.dto.person_filter_dto import (
    FilterPersonQuery,
    PersonFilterDTO,
    PersonSortField,
)
from app.domain.shared.dto.sorter_dto import SortOrderField, SortParams
from app.domain.shared.tree_access import TreeAccessPermissions
from app.infrastructure.repositories.neo4j_family_tree_repository import (
    Neo4jFamilyTreeRepository,
)
from app.infrastructure.storage.minio_object_storage import MinioObjectStorage
from app.presentation.dependencies import get_uow
from app.presentation.mcp.context import get_mcp_caller
from app.utils.app_exception import AppException


def _dump(value: Any) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return json.dumps(value, ensure_ascii=False, default=str)


def _error_payload(exc: AppException) -> str:
    return json.dumps(
        {
            "error": True,
            "code": int(exc.code),
            "status_code": exc.status_code,
            "detail": exc.detail,
        },
        ensure_ascii=False,
    )


async def tool_whoami() -> str:
    """Return the authenticated MCP user (name, username, role, account type)."""
    user = get_mcp_caller()
    uow = get_uow()
    async with uow:
        fresh = await uow.users.get(user.safe_id)
    target = fresh or user
    return _dump(
        {
            "id": str(target.safe_id),
            "username": target.username,
            "fullname": target.fullname,
            "email": target.email,
            "role_id": str(target.role_id) if target.role_id else None,
            "account_type": target.effective_account_type.value,
        }
    )


async def tool_list_trees() -> str:
    """List family trees the caller can access."""
    user = get_mcp_caller()
    uow = get_uow()
    trees = await ListFamilyTreesUseCase(uow).execute(user_id=user.safe_id)
    return _dump([tree.model_dump(mode="json") for tree in trees])


async def tool_search_persons(
    tree_id: str,
    name: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> str:
    """Search people in a tree by name (partial match)."""
    user = get_mcp_caller()
    tid = UUID(tree_id)
    page = max(1, page)
    page_size = min(max(1, page_size), 50)
    offset = (page - 1) * page_size

    uow = get_uow()
    photo = PersonPhotoService(MinioObjectStorage())
    try:
        async with uow:
            await TreeAccessService(uow).require_access(
                tree_id=tid,
                user_id=user.safe_id,
                permission=TreeAccessPermissions.VIEW,
            )
        query = FilterPersonQuery(
            pagination=PaginationParams(
                page=page, page_size=page_size, offset=offset
            ),
            filters=PersonFilterDTO(name=name, tree_id=tid),
            sort=SortParams(
                sort_order=SortOrderField.ASC,
                sort_by=PersonSortField.NAME,
            ),
        )
        result = await GetPersonListByFilterUseCase(uow, photo).execute(
            query, tree_id=tid
        )
        return _dump(result.model_dump(mode="json"))
    except AppException as exc:
        return _error_payload(exc)


async def tool_get_person(tree_id: str, person_id: str) -> str:
    """Fetch one person by id inside a tree."""
    user = get_mcp_caller()
    tid = UUID(tree_id)
    pid = UUID(person_id)
    uow = get_uow()
    photo = PersonPhotoService(MinioObjectStorage())
    try:
        async with uow:
            await TreeAccessService(uow).require_access(
                tree_id=tid,
                user_id=user.safe_id,
                permission=TreeAccessPermissions.VIEW,
            )
        person = await GetPersonUseCase(uow, photo).execute(
            IdDTO(id=pid), tree_id=tid
        )
        return _dump(person.model_dump(mode="json"))
    except AppException as exc:
        return _error_payload(exc)


async def tool_get_person_card(tree_id: str, person_id: str) -> str:
    """Fetch a pedigree card (parents, spouses, children) for one person."""
    user = get_mcp_caller()
    tid = UUID(tree_id)
    pid = UUID(person_id)
    uow = get_uow()
    photo = PersonPhotoService(MinioObjectStorage())
    try:
        async with uow:
            await TreeAccessService(uow).require_access(
                tree_id=tid,
                user_id=user.safe_id,
                permission=TreeAccessPermissions.VIEW,
            )
        card = await GetPersonCardUseCase(uow, photo).execute(
            IdDTO(id=pid), tree_id=tid
        )
        return _dump(card.model_dump(mode="json"))
    except AppException as exc:
        return _error_payload(exc)


async def tool_get_relationship(
    tree_id: str,
    from_person_id: str,
    to_person_id: str,
    male_only: bool = False,
) -> str:
    """Find the closest kinship path between two people in a tree."""
    user = get_mcp_caller()
    tid = UUID(tree_id)
    uow = get_uow()
    try:
        async with uow:
            await TreeAccessService(uow).require_access(
                tree_id=tid,
                user_id=user.safe_id,
                permission=TreeAccessPermissions.VIEW,
            )
        path = await GetClosestRelationshipUseCase(
            Neo4jFamilyTreeRepository(), uow
        ).execute(
            UUID(from_person_id),
            UUID(to_person_id),
            tree_id=tid,
            male_only=male_only,
        )
        return _dump(path.model_dump(mode="json"))
    except AppException as exc:
        return _error_payload(exc)
