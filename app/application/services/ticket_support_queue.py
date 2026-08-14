from collections.abc import Iterable
from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.shared.permissions import Permissions


async def users_can_manage_tickets(
    uow: UnitOfWork, user_ids: Iterable[UUID]
) -> dict[UUID, bool]:
    unique = list(dict.fromkeys(user_ids))
    if not unique:
        return {}

    managers = await uow.users.ids_having_permission(unique, Permissions.TICKET_REPLY)
    return {user_id: user_id in managers for user_id in unique}
