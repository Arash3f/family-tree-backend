import json
from datetime import date
from uuid import UUID

import pytest
from family_tree_api_client import AuthenticatedClient, Client
from family_tree_api_client.api.marriages.create_marriage_family_trees_tree_id_marriages_post import (  # noqa: E501
    asyncio_detailed as create_marriage,
)
from family_tree_api_client.api.marriages.get_marriage_family_trees_tree_id_marriages_marriage_id_get import (  # noqa: E501
    asyncio_detailed as get_marriage,
)
from family_tree_api_client.api.persons.create_person_family_trees_tree_id_persons_post import (  # noqa: E501
    asyncio_detailed as create_person,
)
from family_tree_api_client.api.persons.delete_person_family_trees_tree_id_persons_person_id_delete import (  # noqa: E501
    asyncio_detailed as delete_person,
)
from family_tree_api_client.api.persons.get_closest_relationship_family_trees_tree_id_persons_from_person_id_relation_to_person_id_get import (  # noqa: E501
    asyncio_detailed as get_closest_relationship,
)
from family_tree_api_client.api.persons.get_person_family_trees_tree_id_persons_person_id_get import (  # noqa: E501
    asyncio_detailed as get_person,
)
from family_tree_api_client.api.persons.get_person_list_by_filter_family_trees_tree_id_persons_list_post import (  # noqa: E501
    asyncio_detailed as list_persons,
)
from family_tree_api_client.api.persons.update_person_family_trees_tree_id_persons_put import (  # noqa: E501
    asyncio_detailed as update_person,
)
from family_tree_api_client.models.filter_person_request import FilterPersonRequest
from family_tree_api_client.models.gender import Gender as ApiGender
from family_tree_api_client.models.marriage_create_request import (
    MarriageCreateRequest,
)
from family_tree_api_client.models.paginated_response_person_model import (
    PaginatedResponsePersonModel,
)
from family_tree_api_client.models.pagination_request_params import (
    PaginationRequestParams,
)
from family_tree_api_client.models.person_create_request import PersonCreateRequest
from family_tree_api_client.models.person_sort_field import (
    PersonSortField as ApiPersonSortField,
)
from family_tree_api_client.models.person_update_date_request import (
    PersonUpdateDateRequest,
)
from family_tree_api_client.models.person_update_request import PersonUpdateRequest
from family_tree_api_client.models.person_update_where_request import (
    PersonUpdateWhereRequest,
)
from family_tree_api_client.models.sort_order_field import (
    SortOrderField as ApiSortOrderField,
)
from family_tree_api_client.models.sort_request_params_person_sort_field import (
    SortRequestParamsPersonSortField,
)

from app.domain.entities.marriage import Marriage
from app.domain.entities.person import Gender, Person
from app.utils.error_codes import ErrorCode
from tests.e2e.auth_headers import admin_client as admin_client
from tests.helpers.auth import AuthenticatedUser, create_authenticated_user
from tests.helpers.family_tree import add_tree_member, create_family_tree_with_owner
from tests.helpers.uow import TreeUnitOfWork


def _list_request() -> FilterPersonRequest:
    return FilterPersonRequest(
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParamsPersonSortField(
            sort_by=ApiPersonSortField.ID,
            sort_order=ApiSortOrderField.DESC,
        ),
    )


async def _person_in(uow: TreeUnitOfWork, tree_id: UUID, name: str) -> Person:
    person = await uow.persons.create(
        Person(id=None, tree_id=tree_id, name=name, gender=Gender.MALE)
    )
    await uow.commit()
    return person


async def _outsider(client: Client, uow, asgi_transport) -> AuthenticatedUser:
    """An authenticated user who belongs to no tree at all."""
    return await create_authenticated_user(
        client, uow, permissions=[], asgi_transport=asgi_transport
    )


# ============================================================
# NON-MEMBERS ARE LOCKED OUT OF EVERY TREE-SCOPED ROUTE
# ============================================================


@pytest.mark.asyncio
async def test_non_member_cannot_read_persons_of_a_tree(
    client: Client, tree_id, uow, asgi_transport
):
    outsider = await _outsider(client, uow, asgi_transport)
    person = await _person_in(uow, tree_id, "hidden")

    responses = {
        "list": await list_persons(
            tree_id=tree_id, client=outsider.client, body=_list_request()
        ),
        "get": await get_person(
            tree_id=tree_id, person_id=person.safe_id, client=outsider.client
        ),
    }

    for name, resp in responses.items():
        assert resp.status_code == 403, name
        assert json.loads(resp.content)["error_code"] == int(
            ErrorCode.TREE_MEMBERSHIP_DENIED
        ), name


@pytest.mark.asyncio
async def test_non_member_cannot_write_persons_of_a_tree(
    client: Client, tree_id, uow, asgi_transport
):
    """Read denial is worth little if the write paths stay open."""
    outsider = await _outsider(client, uow, asgi_transport)
    person = await _person_in(uow, tree_id, "untouchable")

    create = await create_person(
        tree_id=tree_id,
        client=outsider.client,
        body=PersonCreateRequest(name="intruder", gender=ApiGender.MALE),
    )
    update = await update_person(
        tree_id=tree_id,
        client=outsider.client,
        body=PersonUpdateRequest(
            data=PersonUpdateDateRequest(name="renamed-by-intruder"),
            where=PersonUpdateWhereRequest(person_id=person.safe_id),
        ),
    )
    delete = await delete_person(
        tree_id=tree_id, person_id=person.safe_id, client=outsider.client
    )

    for resp in (create, update, delete):
        assert resp.status_code == 403
        assert json.loads(resp.content)["error_code"] == int(
            ErrorCode.TREE_MEMBERSHIP_DENIED
        )

    unchanged = await uow.persons.get(person.safe_id)
    assert unchanged is not None
    assert unchanged.name == "untouchable"


@pytest.mark.asyncio
async def test_non_member_cannot_reach_marriages_of_a_tree(
    client: Client, tree_id, uow, asgi_transport
):
    outsider = await _outsider(client, uow, asgi_transport)

    resp = await create_marriage(
        tree_id=tree_id,
        client=outsider.client,
        body=MarriageCreateRequest(
            spouse_a_id=UUID(int=1),
            spouse_b_id=UUID(int=2),
            married_at=date(2020, 1, 1),
        ),
    )

    assert resp.status_code == 403
    assert json.loads(resp.content)["error_code"] == int(
        ErrorCode.TREE_MEMBERSHIP_DENIED
    )


@pytest.mark.asyncio
async def test_non_member_cannot_query_closest_relationship(
    client: Client, tree_id, uow, asgi_transport
):
    outsider = await _outsider(client, uow, asgi_transport)
    a = await _person_in(uow, tree_id, "path-a")
    b = await _person_in(uow, tree_id, "path-b")

    resp = await get_closest_relationship(
        tree_id=tree_id,
        from_person_id=a.safe_id,
        to_person_id=b.safe_id,
        client=outsider.client,
    )

    assert resp.status_code == 403
    assert json.loads(resp.content)["error_code"] == int(
        ErrorCode.TREE_MEMBERSHIP_DENIED
    )


# ============================================================
# MEMBERSHIP IN ONE TREE DOES NOT REACH INTO ANOTHER
# ============================================================


@pytest.mark.asyncio
async def test_member_of_one_tree_cannot_touch_another_tree(
    client: Client, tree_id, uow, asgi_transport
):
    actor = await create_authenticated_user(
        client, uow, permissions=[], asgi_transport=asgi_transport
    )
    await add_tree_member(uow, tree_id=tree_id, user_id=actor.user.safe_id)
    other_tree = await create_family_tree_with_owner(uow, name="Foreign Tree")
    await uow.commit()
    foreigner = await _person_in(uow, other_tree.safe_id, "foreign-person")

    listing = await list_persons(
        tree_id=other_tree.safe_id, client=actor.client, body=_list_request()
    )
    fetch = await get_person(
        tree_id=other_tree.safe_id, person_id=foreigner.safe_id, client=actor.client
    )

    for resp in (listing, fetch):
        assert resp.status_code == 403
        assert json.loads(resp.content)["error_code"] == int(
            ErrorCode.TREE_MEMBERSHIP_DENIED
        )


@pytest.mark.asyncio
async def test_person_from_another_tree_is_invisible_through_your_own_tree(
    client: Client,
    tree_id,
    uow,
    admin_client: AuthenticatedClient,
):
    """The tree in the URL must own the record, even for a member of both trees."""
    from tests.helpers.family_tree import get_admin_user

    admin = await get_admin_user(uow)
    other_tree = await create_family_tree_with_owner(
        uow, owner=admin, name="Admin's Second Tree"
    )
    await uow.commit()
    foreigner = await _person_in(uow, other_tree.safe_id, "belongs-elsewhere")

    resp = await get_person(
        tree_id=tree_id, person_id=foreigner.safe_id, client=admin_client
    )

    assert resp.status_code == 404
    assert json.loads(resp.content)["error_code"] == int(ErrorCode.PERSON_TREE_MISMATCH)


@pytest.mark.asyncio
async def test_person_from_another_tree_cannot_be_updated_through_your_own_tree(
    client: Client,
    tree_id,
    uow,
    admin_client: AuthenticatedClient,
):
    from tests.helpers.family_tree import get_admin_user

    admin = await get_admin_user(uow)
    other_tree = await create_family_tree_with_owner(
        uow, owner=admin, name="Admin's Second Tree"
    )
    await uow.commit()
    foreigner = await _person_in(uow, other_tree.safe_id, "stable-name")

    resp = await update_person(
        tree_id=tree_id,
        client=admin_client,
        body=PersonUpdateRequest(
            data=PersonUpdateDateRequest(name="crossed-over"),
            where=PersonUpdateWhereRequest(person_id=foreigner.safe_id),
        ),
    )

    assert resp.status_code == 404
    assert json.loads(resp.content)["error_code"] == int(ErrorCode.PERSON_TREE_MISMATCH)

    unchanged = await uow.persons.get(foreigner.safe_id)
    assert unchanged is not None
    assert unchanged.name == "stable-name"


@pytest.mark.asyncio
async def test_marriage_from_another_tree_is_invisible_through_your_own_tree(
    client: Client,
    tree_id,
    uow,
    admin_client: AuthenticatedClient,
):
    from tests.helpers.family_tree import get_admin_user

    admin = await get_admin_user(uow)
    other_tree = await create_family_tree_with_owner(
        uow, owner=admin, name="Admin's Second Tree"
    )
    await uow.commit()

    husband = await uow.persons.create(
        Person(
            id=None,
            tree_id=other_tree.safe_id,
            name="foreign-husband",
            gender=Gender.MALE,
            birth_date=date(1980, 1, 1),
        )
    )
    wife = await uow.persons.create(
        Person(
            id=None,
            tree_id=other_tree.safe_id,
            name="foreign-wife",
            gender=Gender.FEMALE,
            birth_date=date(1982, 1, 1),
        )
    )
    marriage = await uow.marriages.create(
        Marriage(
            id=None,
            tree_id=other_tree.safe_id,
            spouse_a_id=husband.safe_id,
            spouse_b_id=wife.safe_id,
            married_at=date(2005, 1, 1),
        )
    )
    await uow.commit()

    resp = await get_marriage(
        tree_id=tree_id, marriage_id=marriage.safe_id, client=admin_client
    )

    assert resp.status_code in (404, 422)
    assert json.loads(resp.content)["error_code"] == int(
        ErrorCode.MARRIAGE_TREE_MISMATCH
    )


@pytest.mark.asyncio
async def test_person_lists_do_not_bleed_between_trees(
    client: Client,
    tree_id,
    uow,
    admin_client: AuthenticatedClient,
):
    from tests.helpers.family_tree import get_admin_user

    admin = await get_admin_user(uow)
    other_tree = await create_family_tree_with_owner(
        uow, owner=admin, name="Admin's Second Tree"
    )
    await uow.commit()
    await _person_in(uow, tree_id, "in-tree-a")
    await _person_in(uow, other_tree.safe_id, "in-tree-b")

    tree_a = await list_persons(
        tree_id=tree_id, client=admin_client, body=_list_request()
    )
    tree_b = await list_persons(
        tree_id=other_tree.safe_id, client=admin_client, body=_list_request()
    )

    assert isinstance(tree_a.parsed, PaginatedResponsePersonModel)
    assert isinstance(tree_b.parsed, PaginatedResponsePersonModel)
    names_a = {item.name for item in tree_a.parsed.items}
    names_b = {item.name for item in tree_b.parsed.items}
    assert "in-tree-a" in names_a and "in-tree-b" not in names_a
    assert "in-tree-b" in names_b and "in-tree-a" not in names_b
