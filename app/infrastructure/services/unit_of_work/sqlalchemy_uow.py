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

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
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

        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type:
            await self.session.rollback()

        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
