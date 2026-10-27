"""Paid plans that lapse: usage, the admin's paid_until, expiry, upgrade tickets."""

from datetime import UTC, date, datetime, timedelta

import pytest
from family_tree_api_client import AuthenticatedClient
from family_tree_api_client.api.auth.me_auth_me_get import asyncio_detailed as me
from family_tree_api_client.api.auth.my_usage_auth_usage_get import (
    asyncio_detailed as my_usage,
)
from family_tree_api_client.api.tickets.create_ticket_tickets_post import (
    asyncio_detailed as create_ticket,
)
from family_tree_api_client.api.users.update_user_users_put import (
    asyncio_detailed as update_user,
)
from family_tree_api_client.models.ticket_category import TicketCategory
from family_tree_api_client.models.ticket_create_request import TicketCreateRequest
from family_tree_api_client.models.usage_response import UsageResponse
from family_tree_api_client.models.user_update_date_request import (
    UserUpdateDateRequest,
)
from family_tree_api_client.models.user_update_request import UserUpdateRequest
from family_tree_api_client.models.user_update_where_request import (
    UserUpdateWhereRequest,
)

from app.core.config import settings
from app.domain.shared.account_type import AccountType
from tests.e2e.auth_headers import admin_client as admin_client
from tests.e2e.auth_headers import member_client as member_client

TODAY = datetime.now(UTC).date()


async def _member_id(uow):
    member = await uow.users.get_by_username("member_user")
    assert member is not None
    return member.safe_id


async def _set_plan(admin_client, user_id, data: dict) -> None:
    response = await update_user(
        client=admin_client,
        body=UserUpdateRequest(
            where=UserUpdateWhereRequest(user_id=user_id),
            data=UserUpdateDateRequest.from_dict(data),
        ),
    )
    assert response.status_code == 200, response.content


@pytest.mark.asyncio
async def test_free_member_usage_reports_the_free_quotas(
    member_client: AuthenticatedClient,
):
    response = await my_usage(client=member_client)

    assert response.status_code == 200, response.content
    usage = response.parsed
    assert isinstance(usage, UsageResponse)
    assert usage.account_type == "free"
    assert usage.limited is True
    assert usage.days_left is None
    assert usage.owned_trees == 0
    assert usage.free_limits.persons_per_tree == settings.FREE_MAX_PERSONS_PER_TREE


@pytest.mark.asyncio
async def test_open_ended_paid_admin_counts_own_trees_without_limits(
    admin_client: AuthenticatedClient,
):
    response = await my_usage(client=admin_client)

    usage = response.parsed
    assert isinstance(usage, UsageResponse)
    assert usage.account_type == "paid"
    assert usage.limited is False
    assert usage.days_left is None
    assert usage.owned_trees == 1
    assert usage.trees[0].name == "E2E Test Tree"
    assert usage.trees[0].persons == 0


@pytest.mark.asyncio
async def test_admin_grants_a_dated_paid_plan(
    admin_client: AuthenticatedClient, member_client: AuthenticatedClient, uow
):
    last_day = TODAY + timedelta(days=29)
    await _set_plan(
        admin_client,
        await _member_id(uow),
        {"account_type": "paid", "paid_until": last_day.isoformat()},
    )

    profile = (await me(client=member_client)).parsed
    usage = (await my_usage(client=member_client)).parsed

    assert profile.account_type == "paid"
    assert profile.paid_until == last_day
    assert usage.limited is False
    assert usage.days_left == 30


@pytest.mark.asyncio
async def test_lapsed_plan_reads_free_before_the_expiry_task_runs(
    admin_client: AuthenticatedClient, member_client: AuthenticatedClient, uow
):
    await _set_plan(
        admin_client,
        await _member_id(uow),
        {"account_type": "paid", "paid_until": (TODAY - timedelta(days=1)).isoformat()},
    )

    profile = (await me(client=member_client)).parsed
    usage = (await my_usage(client=member_client)).parsed

    assert profile.account_type == "free"
    assert usage.limited is True
    # The stored plan is still paid until the daily task rewrites it.
    stored = await uow.users.get_by_username("member_user")
    assert stored.account_type is AccountType.PAID


@pytest.mark.asyncio
async def test_null_paid_until_makes_the_plan_open_ended(
    admin_client: AuthenticatedClient, member_client: AuthenticatedClient, uow
):
    member_id = await _member_id(uow)
    await _set_plan(
        admin_client,
        member_id,
        {"account_type": "paid", "paid_until": date(2000, 1, 1).isoformat()},
    )
    await _set_plan(admin_client, member_id, {"paid_until": None})

    profile = (await me(client=member_client)).parsed

    assert profile.account_type == "paid"
    assert profile.paid_until is None


@pytest.mark.asyncio
async def test_expiry_downgrades_only_lapsed_paid_plans(admin_client, uow):
    member_id = await _member_id(uow)
    await _set_plan(
        admin_client,
        member_id,
        {"account_type": "paid", "paid_until": (TODAY - timedelta(days=1)).isoformat()},
    )

    downgraded = await uow.users.downgrade_lapsed_paid_plans(TODAY)
    await uow.commit()

    assert downgraded == 1
    member = await uow.users.get(member_id)
    assert member.account_type is AccountType.FREE
    # The last covered day stays on record.
    assert member.paid_until == TODAY - timedelta(days=1)
    # The seeded admin's open-ended plan is untouched.
    admin = await uow.users.get_by_username(settings.ADMIN_USERNAME)
    assert admin.account_type is AccountType.PAID


@pytest.mark.asyncio
async def test_member_can_file_an_upgrade_request(member_client: AuthenticatedClient):
    response = await create_ticket(
        client=member_client,
        body=TicketCreateRequest(
            title="Upgrade to the family plan",
            body="Please upgrade my account.",
            category=TicketCategory.UPGRADE_REQUEST,
        ),
    )

    assert response.status_code == 201, response.content
    assert response.parsed.category == TicketCategory.UPGRADE_REQUEST
