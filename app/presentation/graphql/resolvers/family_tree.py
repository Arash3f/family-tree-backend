from uuid import UUID

from strawberry.types import Info

from app.application.dto.family_tree.family_tree_dto import (
    FamilyTreeCreateDTO,
    FamilyTreeUpdateDTO,
    TreeMemberAddDTO,
)
from app.application.use_cases.family_tree.create_family_tree_use_case import (
    CreateFamilyTreeUseCase,
)
from app.application.use_cases.family_tree.get_family_tree_use_case import (
    GetFamilyTreeUseCase,
    ListFamilyTreesUseCase,
)
from app.application.use_cases.family_tree.tree_member_use_cases import (
    AddTreeMemberUseCase,
    ListTreeMembersUseCase,
    RemoveTreeMemberUseCase,
)
from app.application.use_cases.family_tree.update_family_tree_use_case import (
    DeleteFamilyTreeUseCase,
    UpdateFamilyTreeUseCase,
)
from app.domain.shared.permissions import Permissions
from app.presentation.graphql.auth import require_permission
from app.presentation.graphql.types.common import ResultType
from app.presentation.graphql.types.family_tree import (
    FamilyTreeCreateInput,
    FamilyTreeType,
    FamilyTreeUpdateInput,
    TreeMemberAddInput,
    TreeMembershipType,
    family_tree_from_mapping,
    tree_membership_from_mapping,
)

async def resolve_family_trees(info: Info) -> list[FamilyTreeType]:
    user = await require_permission(info, Permissions.TREE_READ)
    usecase = ListFamilyTreesUseCase(info.context.uow)
    res = await usecase.execute(user_id=user.safe_id)
    return [family_tree_from_mapping(item.model_dump()) for item in res]


async def resolve_family_tree(info: Info, tree_id: UUID) -> FamilyTreeType:
    user = await require_permission(info, Permissions.TREE_READ)
    usecase = GetFamilyTreeUseCase(info.context.uow)
    res = await usecase.execute(tree_id=tree_id, user_id=user.safe_id)
    return family_tree_from_mapping(res.model_dump())


async def resolve_tree_members(
    info: Info, tree_id: UUID
) -> list[TreeMembershipType]:
    user = await require_permission(info, Permissions.TREE_READ)
    usecase = ListTreeMembersUseCase(info.context.uow)
    res = await usecase.execute(tree_id=tree_id, user_id=user.safe_id)
    return [tree_membership_from_mapping(item.model_dump()) for item in res]


async def resolve_create_family_tree(
    info: Info, data: FamilyTreeCreateInput
) -> FamilyTreeType:
    user = await require_permission(info, Permissions.TREE_CREATE)
    usecase = CreateFamilyTreeUseCase(info.context.uow)
    res = await usecase.execute(
        FamilyTreeCreateDTO(name=data.name),
        owner_user_id=user.safe_id,
    )
    return family_tree_from_mapping(res.model_dump())


async def resolve_update_family_tree(
    info: Info, tree_id: UUID, data: FamilyTreeUpdateInput
) -> FamilyTreeType:
    user = await require_permission(info, Permissions.TREE_UPDATE)
    usecase = UpdateFamilyTreeUseCase(info.context.uow)
    res = await usecase.execute(
        tree_id=tree_id,
        user_id=user.safe_id,
        dto=FamilyTreeUpdateDTO(name=data.name),
    )
    return family_tree_from_mapping(res.model_dump())


async def resolve_delete_family_tree(info: Info, tree_id: UUID) -> ResultType:
    user = await require_permission(info, Permissions.TREE_DELETE)
    usecase = DeleteFamilyTreeUseCase(info.context.uow)
    await usecase.execute(tree_id=tree_id, user_id=user.safe_id)
    return ResultType(result="ok")


async def resolve_add_tree_member(
    info: Info, tree_id: UUID, data: TreeMemberAddInput
) -> TreeMembershipType:
    user = await require_permission(info, Permissions.TREE_MEMBER_ADD)
    usecase = AddTreeMemberUseCase(info.context.uow)
    res = await usecase.execute(
        tree_id=tree_id,
        actor_user_id=user.safe_id,
        dto=TreeMemberAddDTO(user_id=data.user_id),
    )
    return tree_membership_from_mapping(res.model_dump())


async def resolve_remove_tree_member(
    info: Info, tree_id: UUID, user_id: UUID
) -> ResultType:
    actor = await require_permission(info, Permissions.TREE_MEMBER_REMOVE)
    usecase = RemoveTreeMemberUseCase(info.context.uow)
    await usecase.execute(
        tree_id=tree_id,
        actor_user_id=actor.safe_id,
        target_user_id=user_id,
    )
    return ResultType(result="ok")
