from fastapi import Depends
from strawberry.fastapi import BaseContext

from app.application.interfaces.token_service import TokenService
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.authorization_service import AuthorizationService
from app.domain.services.marriage_rules import MarriageRulesService
from app.domain.services.password_hasher import PasswordHasher
from app.infrastructure.repositories.neo4j_family_tree_repository import (
    Neo4jFamilyTreeRepository,
)
from app.presentation.rest.utils.dependencies import (
    get_authorization_service,
    get_marriage_rule_service,
    get_neo,
    get_password_hasher,
    get_token_service,
    get_uow,
)


class GraphQLContext(BaseContext):
    def __init__(
        self,
        uow: UnitOfWork,
        token_service: TokenService,
        password_hasher: PasswordHasher,
        authorization_service: AuthorizationService,
        neo: Neo4jFamilyTreeRepository,
        marriage_rule_service: MarriageRulesService,
    ):
        super().__init__()
        self.uow = uow
        self.token_service = token_service
        self.password_hasher = password_hasher
        self.authorization_service = authorization_service
        self.neo = neo
        self.marriage_rule_service = marriage_rule_service


async def get_graphql_context(
    uow: UnitOfWork = Depends(get_uow),
    token_service: TokenService = Depends(get_token_service),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    authorization_service: AuthorizationService = Depends(get_authorization_service),
    neo: Neo4jFamilyTreeRepository = Depends(get_neo),
    marriage_rule_service: MarriageRulesService = Depends(get_marriage_rule_service),
) -> GraphQLContext:
    return GraphQLContext(
        uow=uow,
        token_service=token_service,
        password_hasher=password_hasher,
        authorization_service=authorization_service,
        neo=neo,
        marriage_rule_service=marriage_rule_service,
    )
