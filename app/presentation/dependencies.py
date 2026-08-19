"""Composition root: wires infrastructure implementations to application/domain
interfaces via FastAPI's `Depends`.

Shared by both REST routers (`app/presentation/rest/`) and the GraphQL context
(`app/presentation/graphql/context.py`) -- it is not REST-specific.
"""

from fastapi import Depends

from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.authorization_service import AuthorizationService
from app.application.services.person_photo_service import PersonPhotoService
from app.domain.repositories.family_tree_repository import FamilyTreeRepository
from app.domain.repositories.object_storage import ObjectStorage
from app.domain.services.marriage_rules import MarriageRulesService
from app.domain.services.password_hasher import PasswordHasher
from app.infrastructure.database.session import async_session
from app.infrastructure.repositories.neo4j_family_tree_repository import (
    Neo4jFamilyTreeRepository,
)
from app.infrastructure.services.permission_cache_service import (
    PermissionCacheService,
)
from app.infrastructure.services.security.password_hasher_impl import (
    Argon2PasswordHasher,
)
from app.infrastructure.services.security.token_service_imp import JWTService
from app.infrastructure.services.unit_of_work.sqlalchemy_uow import SQLAlchemyUnitOfWork
from app.infrastructure.storage.minio_object_storage import MinioObjectStorage

_permission_cache = PermissionCacheService(ttl_seconds=3600)


def get_uow():
    return SQLAlchemyUnitOfWork(async_session)


async def get_request_uow(uow: UnitOfWork = Depends(get_uow)):
    """Open the unit of work's session once per request and share it.

    FastAPI caches `Depends(get_uow)` results per request, so every consumer
    of this dependency receives the same `UnitOfWork` instance. By entering
    its `async with` block here -- exactly once, at the top of the dependency
    graph -- and yielding the already-entered instance, `get_current_user`,
    `require_tree_member`/`RequireTreeAccess`, and the route handler's use
    case all share one live `AsyncSession`/transaction for the lifetime of
    the request instead of each opening and closing their own.
    """
    async with uow:
        yield uow


def get_neo() -> FamilyTreeRepository:
    return Neo4jFamilyTreeRepository()


def get_object_storage() -> ObjectStorage:
    return MinioObjectStorage()


def get_person_photo_service(
    storage: ObjectStorage = Depends(get_object_storage),
) -> PersonPhotoService:
    return PersonPhotoService(storage)


def get_marriage_rules_service() -> MarriageRulesService:
    return MarriageRulesService()


def get_password_hasher() -> PasswordHasher:
    return Argon2PasswordHasher()


def get_token_service() -> JWTService:
    return JWTService()


def get_permission_cache() -> PermissionCacheService:
    return _permission_cache


def get_authorization_service(
    uow: UnitOfWork = Depends(get_uow),
) -> AuthorizationService:
    """Build an AuthorizationService bound to a fresh, unentered UnitOfWork.

    Used by the GraphQL context (`get_graphql_context`), which manages its
    own session lifecycle via the use case's `async with self.uow:` block.
    REST call sites should use `get_authorization_service_request` instead so
    the permission check shares the single request-scoped session.
    """
    return AuthorizationService(uow)


def get_authorization_service_request(
    uow: UnitOfWork = Depends(get_request_uow),
) -> AuthorizationService:
    return AuthorizationService(uow)
