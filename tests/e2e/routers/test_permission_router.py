import json

import pytest
from family_tree_api_client import AuthenticatedClient, Client
from family_tree_api_client.api.permissions.get_permission_list_by_filter_permissions_list_post import (  # noqa: E501
    asyncio_detailed as get_permission_list_by_filter,
)
from family_tree_api_client.models.filter_permission_request import (
    FilterPermissionRequest,
)
from family_tree_api_client.models.paginated_response_permission_model import (
    PaginatedResponsePermissionModel,
)
from family_tree_api_client.models.pagination_request_params import (
    PaginationRequestParams,
)
from family_tree_api_client.models.permission_sort_field import PermissionSortField
from family_tree_api_client.models.sort_order_field import SortOrderField
from family_tree_api_client.models.sort_request_params_permission_sort_field import (
    SortRequestParamsPermissionSortField,
)

from app.infrastructure.utils.constants.permissions import Permissions
from app.utils.error_codes import ERROR_MESSAGES, ErrorCode
from tests.e2e.auth_headers import admin_client as admin_client
from tests.e2e.auth_headers import member_client as member_client


@pytest.mark.asyncio
async def test_get_permission_list_by_filter_permission_denied(
    member_client: AuthenticatedClient,
):
    data = FilterPermissionRequest(
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParamsPermissionSortField(
            sort_by=PermissionSortField.ID, sort_order=SortOrderField.DESC
        ),
    )
    response = await get_permission_list_by_filter(client=member_client, body=data)
    assert response.status_code == 403
    body = json.loads(response.content)
    assert body["error_code"] == 1301
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]
    assert body["status"] == 403


@pytest.mark.asyncio
async def test_get_permission_list_by_filter_not_authenticated(client: Client):
    data = FilterPermissionRequest(
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParamsPermissionSortField(
            sort_by=PermissionSortField.ID, sort_order=SortOrderField.DESC
        ),
    )
    response = await get_permission_list_by_filter(client=client, body=data)
    assert response.status_code == 401
    assert json.loads(response.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_permission_list_by_filter_success(
    admin_client: AuthenticatedClient,
):
    data = FilterPermissionRequest(
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParamsPermissionSortField(
            sort_by=PermissionSortField.ID, sort_order=SortOrderField.DESC
        ),
    )
    response = await get_permission_list_by_filter(client=admin_client, body=data)
    assert response.status_code == 200
    assert isinstance(response.parsed, PaginatedResponsePermissionModel)
    assert len(response.parsed.items) == Permissions.get_count()
