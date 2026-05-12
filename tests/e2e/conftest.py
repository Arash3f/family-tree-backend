import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.domain.entities.user import User
from app.infrastructure.database.base import Base
from app.infrastructure.database.seed import seed_initial_permissions, seed_initial_user
from app.infrastructure.services.security.password_hasher_impl import (
    Argon2PasswordHasher,
)
from app.infrastructure.services.unit_of_work.sqlalchemy_uow import SQLAlchemyUnitOfWork
from app.main import app
from app.presentation.rest.utils.dependencies import get_uow


@pytest.fixture(scope="session")
def db_engine():
    return create_async_engine(
        settings.database_test_asy,
        echo=False,
        poolclass=NullPool,
    )


@pytest_asyncio.fixture(autouse=True)
async def prepare_database(db_engine):
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

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
        await conn.run_sync(Base.metadata.drop_all)

    await db_engine.dispose()


@pytest_asyncio.fixture
async def uow(db_engine):
    session = AsyncSession(db_engine, expire_on_commit=False)
    uow = SQLAlchemyUnitOfWork(session_factory=lambda: session)

    async with uow:
        yield uow


@pytest_asyncio.fixture(autouse=True)
async def override_uow(uow):
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_uow] = lambda: uow

    yield

    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
