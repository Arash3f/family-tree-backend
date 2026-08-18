from app.application.interfaces.unit_of_work import UnitOfWork
from app.infrastructure.repositories.marriage_repository_sql import (
    SQLMarriageRepository,
)
from app.infrastructure.repositories.permission_repository_sql import (
    SQLPermissionRepository,
)
from app.infrastructure.repositories.person_repository_sql import SQLPersonRepository
from app.infrastructure.repositories.role_repository_sql import SQLRoleRepository
from app.infrastructure.repositories.ticket_message_repository_sql import (
    SQLTicketMessageRepository,
)
from app.infrastructure.repositories.ticket_repository_sql import SQLTicketRepository
from app.infrastructure.repositories.tree_repository_sql import (
    SQLTreeMembershipRepository,
    SQLTreeRepository,
)
from app.infrastructure.repositories.user_repository_sql import SQLUserRepository
from app.infrastructure.repositories.user_session_repository_sql import (
    SQLUserSessionRepository,
)


class SQLAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._enter_depth = 0

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        # Reentrant guard: a single request can legitimately enter the same
        # UnitOfWork instance more than once (e.g. a request-scoped FastAPI
        # dependency opens the session, and a use case further down the call
        # chain does its own `async with self.uow:`). Only the outermost
        # `async with` actually opens/closes the session; nested entries
        # reuse it so callers keep working with one shared transaction
        # instead of silently getting a fresh session each time.
        if self._enter_depth == 0:
            self.session = self.session_factory()

            self.persons = SQLPersonRepository(self.session)
            self.marriages = SQLMarriageRepository(self.session)
            self.users = SQLUserRepository(self.session)
            self.permissions = SQLPermissionRepository(self.session)
            self.roles = SQLRoleRepository(self.session)
            self.sessions = SQLUserSessionRepository(self.session)
            self.tickets = SQLTicketRepository(self.session)
            self.ticket_messages = SQLTicketMessageRepository(self.session)
            self.family_trees = SQLTreeRepository(self.session)
            self.tree_memberships = SQLTreeMembershipRepository(self.session)

        self._enter_depth += 1
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self._enter_depth -= 1

        if self._enter_depth > 0:
            # Still inside an outer `async with self.uow:` block -- let that
            # outer block own rollback/close so it can keep using the
            # session after this nested block exits.
            return

        if exc_type:
            await self.session.rollback()

        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
