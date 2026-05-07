import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.services.unit_of_work import UnitOfWork
from app.domain.repositories.marriage_repository import MarriageRepository
from app.domain.repositories.permission_repository import PermissionRepository
from app.domain.repositories.person_repository import PersonRepository
from app.domain.repositories.role_repository import RoleRepository
from app.domain.repositories.user_repository import UserRepository


@pytest.fixture
def mock_uow():
    permissions_repo = MagicMock(spec_set=PermissionRepository)
    permissions_repo.get_list_by_filter = AsyncMock()

    roles_repo = MagicMock(spec_set=RoleRepository)
    roles_repo.get_list_by_filter = AsyncMock()
    roles_repo.get_or_raise = AsyncMock()

    users_repo = MagicMock(spec_set=UserRepository)
    users_repo.create = AsyncMock()
    users_repo.get_or_raise = AsyncMock()

    persons_repo = MagicMock(spec_set=PersonRepository)
    persons_repo.create = AsyncMock()
    persons_repo.delete = AsyncMock()
    persons_repo.get_or_raise = AsyncMock()

    marriages_repo = MagicMock(spec_set=MarriageRepository)
    marriages_repo.create = AsyncMock()
    marriages_repo.delete = AsyncMock()
    marriages_repo.end = AsyncMock()
    marriages_repo.get_or_raise = AsyncMock()

    uow = MagicMock(spec=UnitOfWork)
    uow.permissions = permissions_repo
    uow.roles = roles_repo
    uow.users = users_repo
    uow.persons = persons_repo
    uow.marriages = marriages_repo

    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)

    uow.commit = AsyncMock()

    return uow
