from datetime import date
from uuid import UUID

import pytest
from pydantic import TypeAdapter

from app.domain.entities.marriage import Marriage
from app.domain.entities.person import Gender, Person
from app.domain.shared.dto.marriage_filter_dto import MarriageSortField
from app.domain.shared.dto.sorter_dto import SortOrderField
from app.infrastructure.services.unit_of_work.sqlalchemy_uow import SQLAlchemyUnitOfWork
from app.presentation.rest.schemas.dto.common import (
    PaginatedResponse,
    PaginationRequestParams,
    ResultResponse,
    SortRequestParams,
)
from app.presentation.rest.schemas.dto.marriage_schema import (
    DivorceRequest,
    FilterMarriageRequest,
    MarriageCreateRequest,
    MarriageCreateResponse,
    MarriageFilterRequestData,
    MarriageGetResponse,
    MarriageModel,
    MarriageUpdateRequest,
    MarriageUpdateResponse,
    _MarriageUpdateDateRequest,
    _MarriageUpdateWhereRequest,
)
from app.utils.error_codes import ERROR_MESSAGES, ErrorCode
from tests.e2e.auth_headers import admin_headers as admin_headers
from tests.e2e.auth_headers import member_headers as member_headers

BASE_URL = "/marriages"


async def _create_spouses(uow: SQLAlchemyUnitOfWork, suffix: str = ""):
    husband = await uow.persons.create(
        Person(
            id=None,
            name=f"husband{suffix}",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
        )
    )
    wife = await uow.persons.create(
        Person(
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
async def test_create_marriage_permission_denied(client, member_headers):  # noqa: F811
    req = MarriageCreateRequest(
        spouse_a_id=UUID(int=1),
        spouse_b_id=UUID(int=2),
        married_at=date(2020, 1, 1),
    )
    resp = await client.post(
        f"{BASE_URL}/",
        json=req.model_dump(mode="json"),
        headers=member_headers,
    )

    assert resp.status_code == 403
    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_create_marriage_unauthenticated(client):
    req = MarriageCreateRequest(
        spouse_a_id=UUID(int=1),
        spouse_b_id=UUID(int=2),
        married_at=date(2020, 1, 1),
    )
    resp = await client.post(
        f"{BASE_URL}/",
        json=req.model_dump(mode="json"),
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_marriage_success(client, admin_headers, uow):  # noqa: F811
    husband, wife = await _create_spouses(uow, suffix="_create")
    await uow.commit()

    req = MarriageCreateRequest(
        spouse_a_id=husband.safe_id,
        spouse_b_id=wife.safe_id,
        married_at=date(2020, 1, 1),
    )

    resp = await client.post(
        f"{BASE_URL}/",
        json=req.model_dump(mode="json"),
        headers=admin_headers,
    )

    assert resp.status_code == 200

    marriage_data = TypeAdapter(MarriageCreateResponse).validate_python(resp.json())
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
async def test_get_marriage_permission_denied(client, member_headers):  # noqa: F811
    resp = await client.get(
        f"{BASE_URL}/{UUID(int=1)}",
        headers=member_headers,
    )

    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_get_marriage_unauthenticated(client):
    resp = await client.get(f"{BASE_URL}/{UUID(int=1)}")

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_marriage_success(client, admin_headers, uow: SQLAlchemyUnitOfWork):  # noqa: F811
    husband, wife = await _create_spouses(uow, suffix="_get")
    marriage = await uow.marriages.create(
        Marriage(
            id=None,
            spouse_a_id=husband.safe_id,
            spouse_b_id=wife.safe_id,
            married_at=date(2020, 1, 1),
        )
    )
    await uow.commit()

    resp = await client.get(
        f"{BASE_URL}/{marriage.safe_id}",
        headers=admin_headers,
    )

    assert resp.status_code == 200

    data = TypeAdapter(MarriageGetResponse).validate_python(resp.json())
    assert data.id == marriage.safe_id
    assert data.spouse_a_id == husband.safe_id
    assert data.spouse_b_id == wife.safe_id


@pytest.mark.asyncio
async def test_get_marriage_with_invalid_id(client, admin_headers):  # noqa: F811
    resp = await client.get(
        f"{BASE_URL}/{UUID(int=999999)}",
        headers=admin_headers,
    )

    assert resp.status_code == 404
    body = resp.json()
    assert body["error_code"] == 1205
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.MARRIAGE_NOT_FOUND]


# ============================================================
# UPDATE MARRIAGE
# ============================================================


@pytest.mark.asyncio
async def test_update_marriage_permission_denied(client, member_headers):  # noqa: F811
    payload = MarriageUpdateRequest(
        where=_MarriageUpdateWhereRequest(marriage_id=UUID(int=1)),
        data=_MarriageUpdateDateRequest(
            spouse_a_id=None,
            spouse_b_id=None,
            married_at=date(2021, 1, 1),
            divorced_at=None,
        ),
    )

    resp = await client.put(
        f"{BASE_URL}/",
        json=payload.model_dump(mode="json"),
        headers=member_headers,
    )

    assert resp.status_code == 403
    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_update_marriage_unauthenticated(client):
    payload = MarriageUpdateRequest(
        where=_MarriageUpdateWhereRequest(marriage_id=UUID(int=1)),
        data=_MarriageUpdateDateRequest(
            spouse_a_id=None,
            spouse_b_id=None,
            married_at=date(2021, 1, 1),
            divorced_at=None,
        ),
    )

    resp = await client.put(
        f"{BASE_URL}/",
        json=payload.model_dump(mode="json"),
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_marriage_success(
    client,
    admin_headers,  # noqa: F811
    uow: SQLAlchemyUnitOfWork,
):
    husband, wife = await _create_spouses(uow, suffix="_update")
    marriage = await uow.marriages.create(
        Marriage(
            id=None,
            spouse_a_id=husband.safe_id,
            spouse_b_id=wife.safe_id,
            married_at=date(2020, 1, 1),
        )
    )
    await uow.commit()

    payload = MarriageUpdateRequest(
        where=_MarriageUpdateWhereRequest(marriage_id=marriage.safe_id),
        data=_MarriageUpdateDateRequest(
            married_at=date(2021, 6, 1),
        ),
    )

    resp = await client.put(
        f"{BASE_URL}/",
        json=payload.model_dump(mode="json", exclude_unset=True),
        headers=admin_headers,
    )

    assert resp.status_code == 200
    TypeAdapter(MarriageUpdateResponse).validate_python(resp.json())

    async with uow:
        updated = await uow.marriages.get_or_raise(marriage_id=marriage.safe_id)

    assert updated.married_at == payload.data.married_at


@pytest.mark.asyncio
async def test_update_marriage_with_invalid_id(client, admin_headers):  # noqa: F811
    payload = MarriageUpdateRequest(
        where=_MarriageUpdateWhereRequest(marriage_id=UUID(int=88888)),
        data=_MarriageUpdateDateRequest(
            married_at=date(2021, 1, 1),
        ),
    )

    resp = await client.put(
        f"{BASE_URL}/",
        json=payload.model_dump(mode="json", exclude_unset=True),
        headers=admin_headers,
    )

    assert resp.status_code == 404
    body = resp.json()
    assert body["error_code"] == 1205
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.MARRIAGE_NOT_FOUND]


# ============================================================
# DELETE MARRIAGE
# ============================================================


@pytest.mark.asyncio
async def test_delete_marriage_permission_denied(client, member_headers):  # noqa: F811
    resp = await client.request(
        "DELETE",
        f"{BASE_URL}/",
        json={"id": str(UUID(int=1))},
        headers=member_headers,
    )

    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_delete_marriage_unauthenticated(client):
    resp = await client.request(
        "DELETE",
        f"{BASE_URL}/",
        json={"id": str(UUID(int=1))},
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_marriage_success(
    client,
    admin_headers,  # noqa: F811
    uow: SQLAlchemyUnitOfWork,
):
    husband, wife = await _create_spouses(uow, suffix="_delete")
    marriage = await uow.marriages.create(
        Marriage(
            id=None,
            spouse_a_id=husband.safe_id,
            spouse_b_id=wife.safe_id,
            married_at=date(2020, 1, 1),
        )
    )
    await uow.commit()

    resp = await client.request(
        "DELETE",
        f"{BASE_URL}/",
        json={"id": str(marriage.safe_id)},
        headers=admin_headers,
    )

    assert resp.status_code == 200
    TypeAdapter(ResultResponse).validate_python(resp.json())

    deleted_marriage_id = marriage.safe_id
    async with uow:
        deleted = await uow.marriages.get(marriage_id=deleted_marriage_id)

    assert deleted is None


@pytest.mark.asyncio
async def test_delete_marriage_with_invalid_id(client, admin_headers):  # noqa: F811
    resp = await client.request(
        "DELETE",
        f"{BASE_URL}/",
        json={"id": str(UUID(int=999999))},
        headers=admin_headers,
    )

    assert resp.status_code == 404
    body = resp.json()
    assert body["error_code"] == 1205
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.MARRIAGE_NOT_FOUND]


# ============================================================
# DIVORCE
# ============================================================


@pytest.mark.asyncio
async def test_divorce_permission_denied(client, member_headers):  # noqa: F811
    req = DivorceRequest(
        marriage_id=UUID(int=1),
        divorced_at=date(2022, 1, 1),
    )

    resp = await client.post(
        f"{BASE_URL}/divorce",
        json=req.model_dump(mode="json"),
        headers=member_headers,
    )

    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_divorce_unauthenticated(client):
    req = DivorceRequest(
        marriage_id=UUID(int=1),
        divorced_at=date(2022, 1, 1),
    )

    resp = await client.post(
        f"{BASE_URL}/divorce",
        json=req.model_dump(mode="json"),
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_divorce_success(client, admin_headers, uow: SQLAlchemyUnitOfWork):  # noqa: F811
    husband, wife = await _create_spouses(uow, suffix="_divorce")
    marriage = await uow.marriages.create(
        Marriage(
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

    resp = await client.post(
        f"{BASE_URL}/divorce",
        json=req.model_dump(mode="json"),
        headers=admin_headers,
    )

    assert resp.status_code == 200
    TypeAdapter(ResultResponse).validate_python(resp.json())

    async with uow:
        updated = await uow.marriages.get_or_raise(marriage_id=marriage.safe_id)

    assert updated.divorced_at == req.divorced_at


@pytest.mark.asyncio
async def test_divorce_with_invalid_id(client, admin_headers):  # noqa: F811
    req = DivorceRequest(
        marriage_id=UUID(int=999999),
        divorced_at=date(2022, 1, 1),
    )

    resp = await client.post(
        f"{BASE_URL}/divorce",
        json=req.model_dump(mode="json"),
        headers=admin_headers,
    )

    assert resp.status_code == 404
    body = resp.json()
    assert body["error_code"] == 1205
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.MARRIAGE_NOT_FOUND]


# ============================================================
# LIST MARRIAGES
# ============================================================


@pytest.mark.asyncio
async def test_get_marriage_list_by_filter_permission_denied(client, member_headers):  # noqa: F811
    req = FilterMarriageRequest(
        filters=MarriageFilterRequestData(),
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParams(
            sort_by=MarriageSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    resp = await client.post(
        f"{BASE_URL}/list",
        json=req.model_dump(mode="json"),
        headers=member_headers,
    )

    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_get_marriage_list_by_filter_unauthenticated(client):
    req = FilterMarriageRequest(
        filters=MarriageFilterRequestData(),
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParams(
            sort_by=MarriageSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    resp = await client.post(
        f"{BASE_URL}/list",
        json=req.model_dump(mode="json"),
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_marriage_list_by_filter_success(
    client,
    admin_headers,  # noqa: F811
    uow: SQLAlchemyUnitOfWork,
):
    marriages = []
    for i in range(5):
        husband, wife = await _create_spouses(uow, suffix=f"_list_{i}")
        marriage = await uow.marriages.create(
            Marriage(
                id=None,
                spouse_a_id=husband.safe_id,
                spouse_b_id=wife.safe_id,
                married_at=date(2020, 1, i + 1),
            )
        )
        marriages.append(marriage)
    await uow.commit()

    req = FilterMarriageRequest(
        filters=MarriageFilterRequestData(),
        pagination=PaginationRequestParams(offset=1, page=2, page_size=2),
        sort=SortRequestParams(
            sort_by=MarriageSortField.ID,
            sort_order=SortOrderField.ASC,
        ),
    )

    resp = await client.post(
        f"{BASE_URL}/list",
        json=req.model_dump(mode="json"),
        headers=admin_headers,
    )

    assert resp.status_code == 200

    data = TypeAdapter(PaginatedResponse[MarriageModel]).validate_python(resp.json())
    sorted_marriages = sorted(marriages, key=lambda marriage: marriage.safe_id)
    start = req.pagination.offset + (req.pagination.page - 1) * req.pagination.page_size
    expected = sorted_marriages[start : start + req.pagination.page_size]

    assert len(data.items) == 2
    assert data.items[0].id == expected[0].safe_id
    assert data.items[1].id == expected[1].safe_id
