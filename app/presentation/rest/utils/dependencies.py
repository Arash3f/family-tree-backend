from fastapi import Depends

from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.authorization_service import AuthorizationService
from app.domain.services.marriage_rules import MarriageRulesService
from app.domain.services.password_hasher import PasswordHasher
from app.infrastructure.database.session import async_session
from app.infrastructure.repositories.neo4j_family_tree_repository import (
    Neo4jFamilyTreeRepository,
)
from app.infrastructure.services.security.password_hasher_impl import (
    Argon2PasswordHasher,
)
from app.infrastructure.services.security.token_service_imp import JWTService
from app.infrastructure.services.unit_of_work.sqlalchemy_uow import SQLAlchemyUnitOfWork


def get_uow():
    return SQLAlchemyUnitOfWork(async_session)


def get_neo() -> Neo4jFamilyTreeRepository:
    return Neo4jFamilyTreeRepository()


def get_marriage_rules_service() -> MarriageRulesService:
    return MarriageRulesService()


def get_marriage_rule_service(
    rules_service: MarriageRulesService = Depends(get_marriage_rules_service),
) -> MarriageRulesService:
    return rules_service


def get_password_hasher() -> PasswordHasher:
    return Argon2PasswordHasher()


def get_token_service() -> JWTService:
    return JWTService()


def get_authorization_service(
    uow: UnitOfWork = Depends(get_uow),
) -> AuthorizationService:
    return AuthorizationService(uow)
