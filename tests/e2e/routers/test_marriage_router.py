import json
from datetime import date
from uuid import UUID

import pytest
from family_tree_api_client import AuthenticatedClient, Client
from family_tree_api_client.api.marriages.create_marriage_family_trees_tree_id_marriages_post import (  # noqa: E501
    asyncio_detailed as create_marriage,
)
from family_tree_api_client.api.marriages.delete_marriage_family_trees_tree_id_marriages_delete import (  # noqa: E501
    asyncio_detailed as delete_marriage,
)
from family_tree_api_client.api.marriages.divorce_family_trees_tree_id_marriages_divorce_post import (  # noqa: E501
    asyncio_detailed as divorce,
)
from family_tree_api_client.api.marriages.get_marriage_family_trees_tree_id_marriages_marriage_id_get import (  # noqa: E501
    asyncio_detailed as get_marriage,
)
from family_tree_api_client.api.marriages.get_marriage_list_by_filter_family_trees_tree_id_marriages_list_post import (  # noqa: E501
    asyncio_detailed as get_marriage_list_by_filter,
)
from family_tree_api_client.api.marriages.update_marriage_family_trees_tree_id_marriages_put import (  # noqa: E501
    asyncio_detailed as update_marriage,
)
from family_tree_api_client.models.divorce_request import DivorceRequest
from family_tree_api_client.models.filter_marriage_request import (
    FilterMarriageRequest,
)
from family_tree_api_client.models.id_request import IdRequest
from family_tree_api_client.models.marriage_create_request import (
    MarriageCreateRequest,
)
from family_tree_api_client.models.marriage_create_response import (
    MarriageCreateResponse,
)
from family_tree_api_client.models.marriage_get_response import MarriageGetResponse
from family_tree_api_client.models.marriage_sort_field import MarriageSortField
from family_tree_api_client.models.marriage_update_date_request import (
    MarriageUpdateDateRequest,
)
from family_tree_api_client.models.marriage_update_request import (
    MarriageUpdateRequest,
)
from family_tree_api_client.models.marriage_update_response import (
    MarriageUpdateResponse,
)
from family_tree_api_client.models.marriage_update_where_request import (
    MarriageUpdateWhereRequest,
)
from family_tree_api_client.models.paginated_response_marriage_model import (
    PaginatedResponseMarriageModel,
)
from family_tree_api_client.models.pagination_request_params import (
    PaginationRequestParams,
)
from family_tree_api_client.models.result_response import ResultResponse
from family_tree_api_client.models.sort_order_field import SortOrderField
from family_tree_api_client.models.sort_request_params_marriage_sort_field import (
    SortRequestParamsMarriageSortField,
)

from app.domain.entities.marriage import Marriage
from app.domain.entities.person import Gender, Person
from app.utils.error_codes import ERROR_MESSAGES, ErrorCode
from tests.e2e.auth_headers import admin_client as admin_client
from tests.e2e.auth_headers import member_client as member_client
from tests.helpers.uow import TreeUnitOfWork


async def _create_spouses(uow: TreeUnitOfWork, suffix: str = ""):
    husband = await uow.persons.create(
        Person(
            tree_id=uow.tree_id,
            id=None,
            name=f"husband{suffix}",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
        )
    )
    wife = await uow.persons.create(
        Person(
            tree_id=uow.tree_id,
            id=None,
            name=f"wife{suffix}",
            gender=Gender.FEMALE,
            birth_date=date(1992, 1, 1),
        )
    )
    return husband, wife


# ============================================================
# CREATE MARRIAGE
# ============================================================


@pytest.mark.asyncio
async def test_create_marriage_permission_denied(
    tree_id, member_client: AuthenticatedClient
):
    req = MarriageCreateRequest(
        spouse_a_id=UUID(int=1),
        spouse_b_id=UUID(int=2),
        married_at=date(2020, 1, 1),
    )
    resp = await create_marriage(tree_id=tree_id, client=member_client, body=req)

    assert resp.status_code == 403
    body = json.loads(resp.content)
    assert body["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.TREE_MEMBERSHIP_DENIED]


@pytest.mark.asyncio
async def test_create_marriage_unauthenticated(client: Client, tree_id):
    req = MarriageCreateRequest(
        spouse_a_id=UUID(int=1),
        spouse_b_id=UUID(int=2),
        married_at=date(2020, 1, 1),
    )
    resp = await create_marriage(tree_id=tree_id, client=client, body=req)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_marriage_success(tree_id, admin_client: AuthenticatedClient, uow):
    husband, wife = await _create_spouses(uow, suffix="_create")
    await uow.commit()

    req = MarriageCreateRequest(
        spouse_a_id=husband.safe_id,
        spouse_b_id=wife.safe_id,
        married_at=date(2020, 1, 1),
    )

    resp = await create_marriage(tree_id=tree_id, client=admin_client, body=req)

    assert resp.status_code == 200

    assert isinstance(resp.parsed, MarriageCreateResponse)
    marriage_data = resp.parsed
    assert marriage_data.id is not None
    assert marriage_data.spouse_a_id == husband.safe_id
    assert marriage_data.spouse_b_id == wife.safe_id
    assert marriage_data.married_at == req.married_at

    async with uow:
        find_marriage = await uow.marriages.get_or_raise(marriage_id=marriage_data.id)

    assert find_marriage.id == marriage_data.id
    assert find_marriage.spouse_a_id == husband.safe_id
    assert find_marriage.spouse_b_id == wife.safe_id


# ============================================================
# GET MARRIAGE
# ============================================================


@pytest.mark.asyncio
async def test_get_marriage_permission_denied(
    tree_id, member_client: AuthenticatedClient
):
    resp = await get_marriage(
        tree_id=tree_id, marriage_id=UUID(int=1), client=member_client
    )

    body = json.loads(resp.content)
    assert body["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.TREE_MEMBERSHIP_DENIED]


@pytest.mark.asyncio
async def test_get_marriage_unauthenticated(client: Client, tree_id):
    resp = await get_marriage(tree_id=tree_id, marriage_id=UUID(int=1), client=client)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_marriage_success(
    tree_id, admin_client: AuthenticatedClient, uow: TreeUnitOfWork
):
    husband, wife = await _create_spouses(uow, suffix="_get")
    marriage = await uow.marriages.create(
        Marriage(
            tree_id=uow.tree_id,
            id=None,
            spouse_a_id=husband.safe_id,
            spouse_b_id=wife.safe_id,
            married_at=date(2020, 1, 1),
        )
    )
    await uow.commit()

    resp = await get_marriage(
        tree_id=tree_id, marriage_id=marriage.safe_id, client=admin_client
    )

    assert resp.status_code == 200

    assert isinstance(resp.parsed, MarriageGetResponse)
    data = resp.parsed
    assert data.id == marriage.safe_id
    assert data.spouse_a_id == husband.safe_id
    assert data.spouse_b_id == wife.safe_id


@pytest.mark.asyncio
async def test_get_marriage_with_invalid_id(tree_id, admin_client: AuthenticatedClient):
    resp = await get_marriage(
        tree_id=tree_id, marriage_id=UUID(int=999999), client=admin_client
    )

    assert resp.status_code == 404
    body = json.loads(resp.content)
    assert body["error_code"] == 1205
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.MARRIAGE_NOT_FOUND]


# ============================================================
# UPDATE MARRIAGE
# ============================================================


@pytest.mark.asyncio
async def test_update_marriage_permission_denied(
    tree_id, member_client: AuthenticatedClient
):
    payload = MarriageUpdateRequest(
        where=MarriageUpdateWhereRequest(marriage_id=UUID(int=1)),
        data=MarriageUpdateDateRequest(
            spouse_a_id=None,
            spouse_b_id=None,
            married_at=date(2021, 1, 1),
            divorced_at=None,
        ),
    )

    resp = await update_marriage(tree_id=tree_id, client=member_client, body=payload)

    body = json.loads(resp.content)
    assert body["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.TREE_MEMBERSHIP_DENIED]


@pytest.mark.asyncio
async def test_update_marriage_unauthenticated(client: Client, tree_id):
    payload = MarriageUpdateRequest(
        where=MarriageUpdateWhereRequest(marriage_id=UUID(int=1)),
        data=MarriageUpdateDateRequest(
            spouse_a_id=None,
            spouse_b_id=None,
            married_at=date(2021, 1, 1),
            divorced_at=None,
        ),
    )

    resp = await update_marriage(tree_id=tree_id, client=client, body=payload)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_marriage_success(
    tree_id,
    admin_client: AuthenticatedClient,
    uow: TreeUnitOfWork,
):
    husband, wife = await _create_spouses(uow, suffix="_update")
    marriage = await uow.marriages.create(
        Marriage(
            tree_id=uow.tree_id,
            id=None,
            spouse_a_id=husband.safe_id,
            spouse_b_id=wife.safe_id,
            married_at=date(2020, 1, 1),
        )
    )
    await uow.commit()

    payload = MarriageUpdateRequest(
        where=MarriageUpdateWhereRequest(marriage_id=marriage.safe_id),
        data=MarriageUpdateDateRequest(
            married_at=date(2021, 6, 1),
        ),
    )

    resp = await update_marriage(tree_id=tree_id, client=admin_client, body=payload)

    assert resp.status_code == 200
    assert isinstance(resp.parsed, MarriageUpdateResponse)

    async with uow:
        updated = await uow.marriages.get_or_raise(marriage_id=marriage.safe_id)

    assert updated.married_at == payload.data.married_at


@pytest.mark.asyncio
async def test_update_marriage_with_invalid_id(
    tree_id, admin_client: AuthenticatedClient
):
    payload = MarriageUpdateRequest(
        where=MarriageUpdateWhereRequest(marriage_id=UUID(int=88888)),
        data=MarriageUpdateDateRequest(
            married_at=date(2021, 1, 1),
        ),
    )

    resp = await update_marriage(tree_id=tree_id, client=admin_client, body=payload)

    assert resp.status_code == 404
    body = json.loads(resp.content)
    assert body["error_code"] == 1205
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.MARRIAGE_NOT_FOUND]


# ============================================================
# DELETE MARRIAGE
# ============================================================


@pytest.mark.asyncio
async def test_delete_marriage_permission_denied(
    tree_id, member_client: AuthenticatedClient
):
    resp = await delete_marriage(
        tree_id=tree_id,
        client=member_client,
        body=IdRequest(id=UUID(int=1)),
    )

    body = json.loads(resp.content)
    assert body["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.TREE_MEMBERSHIP_DENIED]


@pytest.mark.asyncio
async def test_delete_marriage_unauthenticated(client: Client, tree_id):
    resp = await delete_marriage(
        tree_id=tree_id,
        client=client,
        body=IdRequest(id=UUID(int=1)),
    )

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_marriage_success(
    tree_id,
    admin_client: AuthenticatedClient,
    uow: TreeUnitOfWork,
):
    husband, wife = await _create_spouses(uow, suffix="_delete")
    marriage = await uow.marriages.create(
        Marriage(
            tree_id=uow.tree_id,
            id=None,
            spouse_a_id=husband.safe_id,
            spouse_b_id=wife.safe_id,
            married_at=date(2020, 1, 1),
        )
    )
    await uow.commit()

    resp = await delete_marriage(
        tree_id=tree_id,
        client=admin_client,
        body=IdRequest(id=marriage.safe_id),
    )

    assert resp.status_code == 200
    assert isinstance(resp.parsed, ResultResponse)

    deleted_marriage_id = marriage.safe_id
    async with uow:
        deleted = await uow.marriages.get(marriage_id=deleted_marriage_id)

    assert deleted is None


@pytest.mark.asyncio
async def test_delete_marriage_with_invalid_id(
    tree_id, admin_client: AuthenticatedClient
):
    resp = await delete_marriage(
        tree_id=tree_id,
        client=admin_client,
        body=IdRequest(id=UUID(int=999999)),
    )

    assert resp.status_code == 404
    body = json.loads(resp.content)
    assert body["error_code"] == 1205
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.MARRIAGE_NOT_FOUND]


# ============================================================
# DIVORCE
# ============================================================


@pytest.mark.asyncio
async def test_divorce_permission_denied(tree_id, member_client: AuthenticatedClient):
    req = DivorceRequest(
        marriage_id=UUID(int=1),
        divorced_at=date(2022, 1, 1),
    )

    resp = await divorce(tree_id=tree_id, client=member_client, body=req)

    body = json.loads(resp.content)
    assert body["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.TREE_MEMBERSHIP_DENIED]


@pytest.mark.asyncio
async def test_divorce_unauthenticated(client: Client, tree_id):
    req = DivorceRequest(
        marriage_id=UUID(int=1),
        divorced_at=date(2022, 1, 1),
    )

    resp = await divorce(tree_id=tree_id, client=client, body=req)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_divorce_success(
    tree_id, admin_client: AuthenticatedClient, uow: TreeUnitOfWork
):
    husband, wife = await _create_spouses(uow, suffix="_divorce")
    marriage = await uow.marriages.create(
        Marriage(
            tree_id=uow.tree_id,
            id=None,
            spouse_a_id=husband.safe_id,
            spouse_b_id=wife.safe_id,
            married_at=date(2020, 1, 1),
        )
    )
    await uow.commit()

    req = DivorceRequest(
        marriage_id=marriage.safe_id,
        divorced_at=date(2022, 1, 1),
    )

    resp = await divorce(tree_id=tree_id, client=admin_client, body=req)

    assert resp.status_code == 200
    assert isinstance(resp.parsed, ResultResponse)

    async with uow:
        updated = await uow.marriages.get_or_raise(marriage_id=marriage.safe_id)

    assert updated.divorced_at == req.divorced_at


@pytest.mark.asyncio
async def test_divorce_with_invalid_id(tree_id, admin_client: AuthenticatedClient):
    req = DivorceRequest(
        marriage_id=UUID(int=999999),
        divorced_at=date(2022, 1, 1),
    )

    resp = await divorce(tree_id=tree_id, client=admin_client, body=req)

    assert resp.status_code == 404
    body = json.loads(resp.content)
    assert body["error_code"] == 1205
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.MARRIAGE_NOT_FOUND]


# ============================================================
# LIST MARRIAGES
# ============================================================


@pytest.mark.asyncio
async def test_get_marriage_list_by_filter_permission_denied(
    tree_id, member_client: AuthenticatedClient
):
    req = FilterMarriageRequest(
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParamsMarriageSortField(
            sort_by=MarriageSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    resp = await get_marriage_list_by_filter(
        tree_id=tree_id, client=member_client, body=req
    )

    body = json.loads(resp.content)
    assert body["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.TREE_MEMBERSHIP_DENIED]


@pytest.mark.asyncio
async def test_get_marriage_list_by_filter_unauthenticated(client: Client, tree_id):
    req = FilterMarriageRequest(
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParamsMarriageSortField(
            sort_by=MarriageSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    resp = await get_marriage_list_by_filter(tree_id=tree_id, client=client, body=req)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_marriage_list_by_filter_success(
    tree_id,
    admin_client: AuthenticatedClient,
    uow: TreeUnitOfWork,
):
    marriages = []
    for i in range(5):
        husband, wife = await _create_spouses(uow, suffix=f"_list_{i}")
        marriage = await uow.marriages.create(
            Marriage(
                tree_id=uow.tree_id,
                id=None,
                spouse_a_id=husband.safe_id,
                spouse_b_id=wife.safe_id,
                married_at=date(2020, 1, i + 1),
            )
        )
        marriages.append(marriage)
    await uow.commit()

    req = FilterMarriageRequest(
        pagination=PaginationRequestParams(offset=1, page=2, page_size=2),
        sort=SortRequestParamsMarriageSortField(
            sort_by=MarriageSortField.ID,
            sort_order=SortOrderField.ASC,
        ),
    )

    resp = await get_marriage_list_by_filter(
        tree_id=tree_id, client=admin_client, body=req
    )

    assert resp.status_code == 200

    assert isinstance(resp.parsed, PaginatedResponseMarriageModel)
    data = resp.parsed
    sorted_marriages = sorted(marriages, key=lambda marriage: marriage.safe_id)
    start = req.pagination.offset + (req.pagination.page - 1) * req.pagination.page_size
    expected = sorted_marriages[start : start + req.pagination.page_size]

    assert len(data.items) == 2
    assert data.items[0].id == expected[0].safe_id
    assert data.items[1].id == expected[1].safe_id
