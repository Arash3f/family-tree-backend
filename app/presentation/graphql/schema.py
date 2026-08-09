from uuid import UUID

import strawberry
from strawberry.fastapi import GraphQLRouter

from app.presentation.graphql.context import get_graphql_context
from app.presentation.graphql.errors import AppExceptionExtension
from app.presentation.graphql.resolvers import auth as auth_resolvers
from app.presentation.graphql.resolvers import family_tree as family_tree_resolvers
from app.presentation.graphql.resolvers import marriage as marriage_resolvers
from app.presentation.graphql.resolvers import permission as permission_resolvers
from app.presentation.graphql.resolvers import person as person_resolvers
from app.presentation.graphql.resolvers import role as role_resolvers
from app.presentation.graphql.resolvers import ticket as ticket_resolvers
from app.presentation.graphql.resolvers import user as user_resolvers
from app.presentation.graphql.types.common import ResultType
from app.presentation.graphql.types.family_tree import (
    FamilyTreeCreateInput,
    FamilyTreeType,
    FamilyTreeUpdateInput,
    TreeMemberAddInput,
    TreeMembershipType,
)
from app.presentation.graphql.types.marriage import (
    DivorceInput,
    MarriageCreateInput,
    MarriageListInput,
    MarriagePage,
    MarriageType,
    MarriageUpdateInput,
)
from app.presentation.graphql.types.permission import (
    PermissionListInput,
    PermissionPage,
)
from app.presentation.graphql.types.person import (
    ClosestRelationshipType,
    PersonCreateInput,
    PersonListInput,
    PersonPage,
    PersonType,
    PersonUpdateInput,
)
from app.presentation.graphql.types.role import (
    RoleCreateInput,
    RoleListInput,
    RolePage,
    RoleType,
    RoleUpdateInput,
)
from app.presentation.graphql.types.ticket import (
    TicketCreateInput,
    TicketListInput,
    TicketMessageCreateInput,
    TicketMessageType,
    TicketPage,
    TicketSummaryType,
    TicketType,
    TicketUpdateStatusInput,
)
from app.presentation.graphql.types.user import (
    AuthTokensType,
    UserCreateInput,
    UserListInput,
    UserPage,
    UserType,
    UserUpdateInput,
)


@strawberry.type
class Query:
    @strawberry.field(description="Current authenticated user (REST: GET /auth/me)")
    async def me(self, info: strawberry.Info) -> UserType:
        return await auth_resolvers.resolve_me(info)

    @strawberry.field(description="List family trees for current user (REST: GET /family-trees)")
    async def family_trees(self, info: strawberry.Info) -> list[FamilyTreeType]:
        return await family_tree_resolvers.resolve_family_trees(info)

    @strawberry.field(description="Get family tree by id (REST: GET /family-trees/{id})")
    async def family_tree(
        self, info: strawberry.Info, tree_id: UUID
    ) -> FamilyTreeType:
        return await family_tree_resolvers.resolve_family_tree(info, tree_id)

    @strawberry.field(
        description="List tree members (REST: GET /family-trees/{id}/members)"
    )
    async def tree_members(
        self, info: strawberry.Info, tree_id: UUID
    ) -> list[TreeMembershipType]:
        return await family_tree_resolvers.resolve_tree_members(info, tree_id)

    @strawberry.field(
        description="Get person by id (REST: GET /family-trees/{tree_id}/persons/{id})"
    )
    async def person(
        self, info: strawberry.Info, tree_id: UUID, person_id: UUID
    ) -> PersonType:
        return await person_resolvers.resolve_person(info, tree_id, person_id)

    @strawberry.field(
        description="Filtered person list (REST: POST /family-trees/{tree_id}/persons/list)"
    )
    async def persons(
        self,
        info: strawberry.Info,
        tree_id: UUID,
        data: PersonListInput | None = None,
    ) -> PersonPage:
        return await person_resolvers.resolve_persons(info, tree_id, data)

    @strawberry.field(
        description="Closest relationship path (REST: GET /family-trees/{tree_id}/persons/{from}/relation/{to})"
    )
    async def closest_relationship(
        self,
        info: strawberry.Info,
        tree_id: UUID,
        from_person_id: UUID,
        to_person_id: UUID,
    ) -> ClosestRelationshipType:
        return await person_resolvers.resolve_closest_relationship(
            info, tree_id, from_person_id, to_person_id
        )

    @strawberry.field(description="Get user by id (REST: GET /users/{id})")
    async def user(self, info: strawberry.Info, user_id: UUID) -> UserType:
        return await user_resolvers.resolve_user(info, user_id)

    @strawberry.field(description="Filtered user list (REST: POST /users/list)")
    async def users(
        self,
        info: strawberry.Info,
        data: UserListInput | None = None,
    ) -> UserPage:
        return await user_resolvers.resolve_users(info, data)

    @strawberry.field(description="Get role by id (REST: GET /roles/{id})")
    async def role(self, info: strawberry.Info, role_id: UUID) -> RoleType:
        return await role_resolvers.resolve_role(info, role_id)

    @strawberry.field(description="Filtered role list (REST: POST /roles/list)")
    async def roles(
        self,
        info: strawberry.Info,
        data: RoleListInput | None = None,
    ) -> RolePage:
        return await role_resolvers.resolve_roles(info, data)

    @strawberry.field(
        description="Filtered permission list (REST: POST /permissions/list)"
    )
    async def permissions(
        self,
        info: strawberry.Info,
        data: PermissionListInput | None = None,
    ) -> PermissionPage:
        return await permission_resolvers.resolve_permissions(info, data)

    @strawberry.field(
        description="Get marriage by id (REST: GET /family-trees/{tree_id}/marriages/{id})"
    )
    async def marriage(
        self, info: strawberry.Info, tree_id: UUID, marriage_id: UUID
    ) -> MarriageType:
        return await marriage_resolvers.resolve_marriage(info, tree_id, marriage_id)

    @strawberry.field(
        description="Filtered marriage list (REST: POST /family-trees/{tree_id}/marriages/list)"
    )
    async def marriages(
        self,
        info: strawberry.Info,
        tree_id: UUID,
        data: MarriageListInput | None = None,
    ) -> MarriagePage:
        return await marriage_resolvers.resolve_marriages(info, tree_id, data)

    @strawberry.field(description="Get ticket by id (REST: GET /tickets/{id})")
    async def ticket(self, info: strawberry.Info, ticket_id: UUID) -> TicketType:
        return await ticket_resolvers.resolve_ticket(info, ticket_id)

    @strawberry.field(description="Filtered ticket list (REST: POST /tickets/list)")
    async def tickets(
        self,
        info: strawberry.Info,
        data: TicketListInput | None = None,
    ) -> TicketPage:
        return await ticket_resolvers.resolve_tickets(info, data)


@strawberry.type
class Mutation:
    @strawberry.mutation(description="Login (REST: POST /auth/login)")
    async def login(
        self,
        info: strawberry.Info,
        username: str,
        password: str,
    ) -> AuthTokensType:
        return await auth_resolvers.resolve_login(info, username, password)

    @strawberry.mutation(description="Refresh tokens (REST: POST /auth/refresh)")
    async def refresh_token(
        self,
        info: strawberry.Info,
        refresh_token: str,
    ) -> AuthTokensType:
        return await auth_resolvers.resolve_refresh_token(info, refresh_token)

    @strawberry.mutation(description="Logout current session (REST: POST /auth/logout)")
    async def logout(self, info: strawberry.Info) -> ResultType:
        return await auth_resolvers.resolve_logout(info)

    @strawberry.mutation(
        description="Logout all sessions (REST: POST /auth/logout-all)"
    )
    async def logout_all(self, info: strawberry.Info) -> ResultType:
        return await auth_resolvers.resolve_logout_all(info)

    @strawberry.mutation(description="Create family tree (REST: POST /family-trees)")
    async def create_family_tree(
        self,
        info: strawberry.Info,
        data: FamilyTreeCreateInput,
    ) -> FamilyTreeType:
        return await family_tree_resolvers.resolve_create_family_tree(info, data)

    @strawberry.mutation(
        description="Update family tree (REST: PATCH /family-trees/{id})"
    )
    async def update_family_tree(
        self,
        info: strawberry.Info,
        tree_id: UUID,
        data: FamilyTreeUpdateInput,
    ) -> FamilyTreeType:
        return await family_tree_resolvers.resolve_update_family_tree(
            info, tree_id, data
        )

    @strawberry.mutation(
        description="Delete family tree (REST: DELETE /family-trees/{id})"
    )
    async def delete_family_tree(
        self, info: strawberry.Info, tree_id: UUID
    ) -> ResultType:
        return await family_tree_resolvers.resolve_delete_family_tree(info, tree_id)

    @strawberry.mutation(
        description="Add tree member (REST: POST /family-trees/{id}/members)"
    )
    async def add_tree_member(
        self,
        info: strawberry.Info,
        tree_id: UUID,
        data: TreeMemberAddInput,
    ) -> TreeMembershipType:
        return await family_tree_resolvers.resolve_add_tree_member(
            info, tree_id, data
        )

    @strawberry.mutation(
        description="Remove tree member (REST: DELETE /family-trees/{id}/members/{user_id})"
    )
    async def remove_tree_member(
        self, info: strawberry.Info, tree_id: UUID, user_id: UUID
    ) -> ResultType:
        return await family_tree_resolvers.resolve_remove_tree_member(
            info, tree_id, user_id
        )

    @strawberry.mutation(
        description="Create person (REST: POST /family-trees/{tree_id}/persons/)"
    )
    async def create_person(
        self,
        info: strawberry.Info,
        tree_id: UUID,
        data: PersonCreateInput,
    ) -> PersonType:
        return await person_resolvers.resolve_create_person(info, tree_id, data)

    @strawberry.mutation(
        description="Update person (REST: PUT /family-trees/{tree_id}/persons/)"
    )
    async def update_person(
        self,
        info: strawberry.Info,
        tree_id: UUID,
        data: PersonUpdateInput,
    ) -> PersonType:
        return await person_resolvers.resolve_update_person(info, tree_id, data)

    @strawberry.mutation(
        description="Delete person (REST: DELETE /family-trees/{tree_id}/persons/{id})"
    )
    async def delete_person(
        self,
        info: strawberry.Info,
        tree_id: UUID,
        person_id: UUID,
    ) -> ResultType:
        return await person_resolvers.resolve_delete_person(info, tree_id, person_id)

    @strawberry.mutation(description="Create user (REST: POST /users/)")
    async def create_user(
        self,
        info: strawberry.Info,
        data: UserCreateInput,
    ) -> UserType:
        return await user_resolvers.resolve_create_user(info, data)

    @strawberry.mutation(description="Update user (REST: PUT /users/)")
    async def update_user(
        self,
        info: strawberry.Info,
        data: UserUpdateInput,
    ) -> UserType:
        return await user_resolvers.resolve_update_user(info, data)

    @strawberry.mutation(description="Delete user (REST: DELETE /users/{id})")
    async def delete_user(
        self,
        info: strawberry.Info,
        user_id: UUID,
    ) -> ResultType:
        return await user_resolvers.resolve_delete_user(info, user_id)

    @strawberry.mutation(description="Create role (REST: POST /roles/)")
    async def create_role(
        self,
        info: strawberry.Info,
        data: RoleCreateInput,
    ) -> RoleType:
        return await role_resolvers.resolve_create_role(info, data)

    @strawberry.mutation(description="Update role (REST: PUT /roles/)")
    async def update_role(
        self,
        info: strawberry.Info,
        data: RoleUpdateInput,
    ) -> RoleType:
        return await role_resolvers.resolve_update_role(info, data)

    @strawberry.mutation(description="Delete role (REST: DELETE /roles/{id})")
    async def delete_role(
        self,
        info: strawberry.Info,
        role_id: UUID,
    ) -> ResultType:
        return await role_resolvers.resolve_delete_role(info, role_id)

    @strawberry.mutation(
        description="Create marriage (REST: POST /family-trees/{tree_id}/marriages/)"
    )
    async def create_marriage(
        self,
        info: strawberry.Info,
        tree_id: UUID,
        data: MarriageCreateInput,
    ) -> MarriageType:
        return await marriage_resolvers.resolve_create_marriage(info, tree_id, data)

    @strawberry.mutation(
        description="Update marriage (REST: PUT /family-trees/{tree_id}/marriages/)"
    )
    async def update_marriage(
        self,
        info: strawberry.Info,
        tree_id: UUID,
        data: MarriageUpdateInput,
    ) -> MarriageType:
        return await marriage_resolvers.resolve_update_marriage(info, tree_id, data)

    @strawberry.mutation(
        description="Delete marriage (REST: DELETE /family-trees/{tree_id}/marriages/)"
    )
    async def delete_marriage(
        self,
        info: strawberry.Info,
        tree_id: UUID,
        marriage_id: UUID,
    ) -> ResultType:
        return await marriage_resolvers.resolve_delete_marriage(
            info, tree_id, marriage_id
        )

    @strawberry.mutation(
        description="Divorce (REST: POST /family-trees/{tree_id}/marriages/divorce)"
    )
    async def divorce(
        self,
        info: strawberry.Info,
        tree_id: UUID,
        data: DivorceInput,
    ) -> ResultType:
        return await marriage_resolvers.resolve_divorce(info, tree_id, data)

    @strawberry.mutation(description="Create ticket (REST: POST /tickets/)")
    async def create_ticket(
        self,
        info: strawberry.Info,
        data: TicketCreateInput,
    ) -> TicketType:
        return await ticket_resolvers.resolve_create_ticket(info, data)

    @strawberry.mutation(
        description="Add ticket message (REST: POST /tickets/{id}/messages)"
    )
    async def add_ticket_message(
        self,
        info: strawberry.Info,
        ticket_id: UUID,
        data: TicketMessageCreateInput,
    ) -> TicketMessageType:
        return await ticket_resolvers.resolve_add_ticket_message(
            info, ticket_id, data
        )

    @strawberry.mutation(
        description="Update ticket status (REST: PATCH /tickets/{id}/status)"
    )
    async def update_ticket_status(
        self,
        info: strawberry.Info,
        ticket_id: UUID,
        data: TicketUpdateStatusInput,
    ) -> TicketSummaryType:
        return await ticket_resolvers.resolve_update_ticket_status(
            info, ticket_id, data
        )


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[AppExceptionExtension],
)

graphql_router = GraphQLRouter(
    schema,
    path="/graphql",
    context_getter=get_graphql_context,
    graphql_ide="graphiql",
)
