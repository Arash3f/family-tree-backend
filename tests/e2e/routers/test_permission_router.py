import pytest
from httpx import Response
from pydantic import TypeAdapter

from app.domain.shared.dto.permission_filter_dto import PermissionSortField
from app.domain.shared.dto.sorter_dto import SortOrderField
from app.infrastructure.utils.constants.permissions import Permissions
from app.presentation.rest.schemas.dto.common import (
    PaginatedResponse,
    PaginationRequestParams,
    SortRequestParams,
)
from app.presentation.rest.schemas.dto.permission_schema import (
    FilterPermissionRequest,
    PermissionModel,
)
from app.utils.error_codes import ERROR_MESSAGES, ErrorCode
from tests.e2e.auth_headers import admin_headers as admin_headers
from tests.e2e.auth_headers import member_headers as member_headers


@pytest.mark.asyncio
async def test_get_permission_list_by_filter_permission_denied(client, member_headers):  # noqa: F811
    data: FilterPermissionRequest = FilterPermissionRequest(
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParams(
            sort_by=PermissionSortField.ID, sort_order=SortOrderField.DESC
        ),
    )
    response: Response = await client.post(
        "/permissions/list",
        json=data.model_dump(),
        headers=member_headers,
    )
    assert response.status_code == 403
    assert response.json()["error_code"] == 1301
    assert (
        response.json()["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]
    )
    assert response.json()["status"] == 403


@pytest.mark.asyncio
async def test_get_permission_list_by_filter_not_authenticated(client):
    data: FilterPermissionRequest = FilterPermissionRequest(
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParams(
            sort_by=PermissionSortField.ID, sort_order=SortOrderField.DESC
        ),
    )
    response: Response = await client.post(
        "/permissions/list",
        json=data.model_dump(),
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_permission_list_by_filter_success(client, admin_headers):  # noqa: F811
    data: FilterPermissionRequest = FilterPermissionRequest(
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParams(
            sort_by=PermissionSortField.ID, sort_order=SortOrderField.DESC
        ),
    )
    response = await client.post(
        "/permissions/list",
        json=data.model_dump(),
        headers=admin_headers,
    )
    assert response.status_code == 200
    adapter = TypeAdapter(PaginatedResponse[PermissionModel])
    response_data = adapter.validate_python(response.json())
    assert len(response_data.items) == Permissions.get_count()
