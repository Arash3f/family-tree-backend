from app.application.interfaces.unit_of_work import UnitOfWork
from app.infrastructure.repositories.marriage_repository_sql import (
    SQLMarriageRepository,
)
from app.infrastructure.repositories.permission_repository_sql import (
    SQLPermissionRepository,
)
from app.infrastructure.repositories.person_repository_sql import SQLPersonRepository
from app.infrastructure.repositories.role_repository_sql import SQLRoleRepository
from app.infrastructure.repositories.user_repository_sql import SQLUserRepository


class SQLAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        self.session = self.session_factory()

        # ! Add Repositories
        self.persons = SQLPersonRepository(self.session)
        self.marriages = SQLMarriageRepository(self.session)
        self.users = SQLUserRepository(self.session)
        self.permissions = SQLPermissionRepository(self.session)
        self.roles = SQLRoleRepository(self.session)

        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type:
            await self.session.rollback()

        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
