from fastapi import Depends
from strawberry.fastapi import BaseContext

from app.application.interfaces.token_service import TokenService
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.authorization_service import AuthorizationService
from app.application.services.person_photo_service import PersonPhotoService
from app.domain.repositories.family_tree_repository import FamilyTreeRepository
from app.domain.services.marriage_rules import MarriageRulesService
from app.domain.services.password_hasher import PasswordHasher
from app.presentation.rest.utils.dependencies import (
    get_authorization_service_request,
    get_marriage_rules_service,
    get_neo,
    get_password_hasher,
    get_person_photo_service,
    get_request_uow,
    get_token_service,
)


class GraphQLContext(BaseContext):
    def __init__(
        self,
        uow: UnitOfWork,
        token_service: TokenService,
        password_hasher: PasswordHasher,
        authorization_service: AuthorizationService,
        neo: FamilyTreeRepository,
        marriage_rule_service: MarriageRulesService,
        photo_service: PersonPhotoService,
    ):
        super().__init__()
        self.uow = uow
        self.token_service = token_service
        self.password_hasher = password_hasher
        self.authorization_service = authorization_service
        self.neo = neo
        self.marriage_rule_service = marriage_rule_service
        self.photo_service = photo_service


async def get_graphql_context(
    uow: UnitOfWork = Depends(get_request_uow),
    token_service: TokenService = Depends(get_token_service),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    authorization_service: AuthorizationService = Depends(
        get_authorization_service_request
    ),
    neo: FamilyTreeRepository = Depends(get_neo),
    marriage_rule_service: MarriageRulesService = Depends(get_marriage_rules_service),
    photo_service: PersonPhotoService = Depends(get_person_photo_service),
) -> GraphQLContext:
    """Build the per-request GraphQL context on the shared request-scoped uow.

    `get_request_uow` enters the session once for the whole request (see its
    docstring); every resolver's `async with ctx.uow:` -- and the auth/
    tree-access checks in `graphql/auth.py` and `graphql/tree_access.py` --
    then become nested entries into that same open session instead of each
    opening and closing their own, mirroring the REST-side fix.
    """
    return GraphQLContext(
        uow=uow,
        token_service=token_service,
        password_hasher=password_hasher,
        authorization_service=authorization_service,
        neo=neo,
        marriage_rule_service=marriage_rule_service,
        photo_service=photo_service,
    )
