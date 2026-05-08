# import pytest
# import pytest_asyncio

# from httpx import ASGITransport, AsyncClient
# from sqlalchemy.ext.asyncio import (
#     AsyncSession,
#     async_sessionmaker,
#     create_async_engine,
# )
# from sqlalchemy.pool import NullPool

# from app.infrastructure.database.seed import seed_initial_permissions, seed_initial_user
# from app.infrastructure.security.password_hasher_impl import Argon2PasswordHasher
# from app.presentation.rest.utils.dependencies import get_uow
# from app.main import app
# from app.core.config import setting
# from app.infrastructure.database.base import Base
# from app.infrastructure.unit_of_work.sqlalchemy_uow import SQLAlchemyUnitOfWork


# @pytest.fixture(scope="session")
# def db_engine():
#     return create_async_engine(
#         setting.database_test_asy,
#         echo=False,
#         poolclass=NullPool,
#     )


# @pytest.fixture(scope="session")
# async def seed_database(db_engine):
#     session_factory = async_sessionmaker(
#         bind=db_engine,
#         class_=AsyncSession,
#         expire_on_commit=False,
#     )

#     uow = SQLAlchemyUnitOfWork(session_factory=session_factory)
#     password_hasher = Argon2PasswordHasher()

#     await seed_initial_permissions(uow=uow)
#     await seed_initial_user(uow=uow, password_hasher=password_hasher)


# @pytest_asyncio.fixture(scope="session", autouse=True)
# async def prepare_database(db_engine):
#     async with db_engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)

#     yield

#     async with db_engine.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all)

#     await db_engine.dispose()


# @pytest_asyncio.fixture
# async def db_connection(db_engine):
#     async with db_engine.connect() as connection:
#         transaction = await connection.begin()
#         try:
#             yield connection
#         finally:
#             await transaction.rollback()


# @pytest_asyncio.fixture
# async def session_factory(db_connection):
#     return async_sessionmaker(
#         bind=db_connection,
#         class_=AsyncSession,
#         expire_on_commit=False,
#     )


# @pytest_asyncio.fixture
# async def override_get_uow(session_factory):
#     async def _get_test_uow():
#         async with SQLAlchemyUnitOfWork(session_factory=session_factory) as uow:
#             yield uow

#     app.dependency_overrides[get_uow] = _get_test_uow
#     yield
#     app.dependency_overrides.pop(get_uow, None)


# @pytest_asyncio.fixture
# async def client(override_get_uow):
#     transport = ASGITransport(app=app)

#     async with AsyncClient(
#         transport=transport,
#         base_url="http://127.0.0.1:8001",
#     ) as ac:
#         yield ac
