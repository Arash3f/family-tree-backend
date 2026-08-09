import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.domain.entities.user import User
from app.infrastructure.database.base import Base
from app.infrastructure.database.parent_integrity_ddl import install_parent_integrity_ddl
from app.infrastructure.database.seed import seed_initial_permissions, seed_initial_user
from app.infrastructure.services.security.password_hasher_impl import (
    Argon2PasswordHasher,
)
from app.infrastructure.services.unit_of_work.sqlalchemy_uow import SQLAlchemyUnitOfWork
from app.main import app
from app.presentation.rest.utils.dependencies import get_uow
from tests.helpers.family_tree import create_family_tree_with_owner, get_admin_user

# Avoid cross-test auth rate-limit bleed (shared client IP in ASGI tests)
settings.AUTH_RATE_LIMIT_PER_MINUTE = 0


@pytest.fixture(scope="session")
def db_engine():
    return create_async_engine(
        settings.database_test_asy,
        echo=False,
        poolclass=NullPool,
    )


async def _reset_schema(conn) -> None:
    # Cascade avoids DROP failures when persons ↔ marriages form an FK cycle.
    await conn.execute(text("DROP SCHEMA public CASCADE"))
    await conn.execute(text("CREATE SCHEMA public"))


@pytest_asyncio.fixture(autouse=True)
async def prepare_database(db_engine):
    async with db_engine.begin() as conn:
        await _reset_schema(conn)
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(install_parent_integrity_ddl)

        async_session = async_sessionmaker(
            conn, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            uow = SQLAlchemyUnitOfWork(session_factory=lambda: session)
            password_hasher = Argon2PasswordHasher()

            await seed_initial_permissions(uow=uow)
            await seed_initial_user(uow=uow, password_hasher=password_hasher)
            username = "member_user"
            password = "member_user"

            hasher = Argon2PasswordHasher()
            hashed_password = hasher.hash(password)

            user = User(
                username=username,
                password_hash=hashed_password,
            )
            await uow.users.create(user)

    yield

    async with db_engine.begin() as conn:
        await _reset_schema(conn)


@pytest_asyncio.fixture
async def uow(db_engine, prepare_database):
    session = AsyncSession(db_engine, expire_on_commit=False)
    uow = SQLAlchemyUnitOfWork(session_factory=lambda: session)

    async with uow:
        admin = await get_admin_user(uow)
        tree = await create_family_tree_with_owner(
            uow, owner=admin, name="E2E Test Tree"
        )
        await uow.commit()
        uow.tree_id = tree.safe_id
        yield uow


@pytest_asyncio.fixture
async def tree_id(uow):
    return uow.tree_id


@pytest_asyncio.fixture(autouse=True)
async def override_uow(uow):
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_uow] = lambda: uow

    yield

    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)


@pytest.fixture(autouse=True)
def stub_family_tree_sync(monkeypatch):
    """Avoid Redis/Celery side effects during API e2e tests."""
    from app.application.services.family_tree_sync_service import FamilyTreeSyncService

    def _noop(self, *args, **kwargs):
        return None

    for method_name in (
        "upsert_person",
        "update_person",
        "delete_person",
        "upsert_spouse",
        "remove_spouse",
        "replace_spouse",
    ):
        monkeypatch.setattr(FamilyTreeSyncService, method_name, _noop)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
