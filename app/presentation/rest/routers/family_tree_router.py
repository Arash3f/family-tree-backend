from uuid import UUID

from fastapi import APIRouter, Depends

from app.application.dto.family_tree.family_tree_dto import (
    FamilyTreeCreateDTO,
    FamilyTreeUpdateDTO,
    TreeMemberAddDTO,
    TreeMemberUpdateDTO,
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
    UpdateTreeMemberUseCase,
)
from app.application.use_cases.family_tree.update_family_tree_use_case import (
    DeleteFamilyTreeUseCase,
    UpdateFamilyTreeUseCase,
)
from app.domain.entities.user import User
from app.domain.shared.permissions import Permissions
from app.presentation.rest.dependencies.auth_dependencies import get_current_user
from app.presentation.rest.dependencies.permission_guard import RequirePermission
from app.presentation.rest.dependencies.tree_guard import (
    require_tree_member_add,
    require_tree_member_remove,
)
from app.presentation.rest.schemas.dto.common import ResultResponse
from app.presentation.rest.schemas.dto.family_tree_schema import (
    FamilyTreeCreateRequest,
    FamilyTreeResponse,
    FamilyTreeUpdateRequest,
    TreeMemberAddRequest,
    TreeMemberUpdateRequest,
    TreeMembershipResponse,
)
from app.presentation.rest.utils.dependencies import get_uow

router = APIRouter(prefix="/family-trees", tags=["Family Trees"])


@router.post(
    "",
    response_model=FamilyTreeResponse,
    dependencies=[Depends(RequirePermission(Permissions.TREE_CREATE))],
    status_code=201,
)
async def create_family_tree(
    data: FamilyTreeCreateRequest,
    current_user: User = Depends(get_current_user),
    uow=Depends(get_uow),
) -> FamilyTreeResponse:
    usecase = CreateFamilyTreeUseCase(uow)
    res = await usecase.execute(
        FamilyTreeCreateDTO(name=data.name),
        owner_user_id=current_user.safe_id,
    )
    return FamilyTreeResponse.model_validate(res.model_dump())


@router.get(
    "",
    response_model=list[FamilyTreeResponse],
    dependencies=[Depends(RequirePermission(Permissions.TREE_READ))],
)
async def list_family_trees(
    current_user: User = Depends(get_current_user),
    uow=Depends(get_uow),
) -> list[FamilyTreeResponse]:
    usecase = ListFamilyTreesUseCase(uow)
    res = await usecase.execute(user_id=current_user.safe_id)
    return [FamilyTreeResponse.model_validate(item.model_dump()) for item in res]


@router.get(
    "/{tree_id}",
    response_model=FamilyTreeResponse,
    dependencies=[Depends(RequirePermission(Permissions.TREE_READ))],
)
async def get_family_tree(
    tree_id: UUID,
    current_user: User = Depends(get_current_user),
    uow=Depends(get_uow),
) -> FamilyTreeResponse:
    usecase = GetFamilyTreeUseCase(uow)
    res = await usecase.execute(tree_id=tree_id, user_id=current_user.safe_id)
    return FamilyTreeResponse.model_validate(res.model_dump())


@router.patch(
    "/{tree_id}",
    response_model=FamilyTreeResponse,
    dependencies=[Depends(RequirePermission(Permissions.TREE_UPDATE))],
)
async def update_family_tree(
    tree_id: UUID,
    data: FamilyTreeUpdateRequest,
    current_user: User = Depends(get_current_user),
    uow=Depends(get_uow),
) -> FamilyTreeResponse:
    usecase = UpdateFamilyTreeUseCase(uow)
    res = await usecase.execute(
        tree_id=tree_id,
        user_id=current_user.safe_id,
        dto=FamilyTreeUpdateDTO(name=data.name),
    )
    return FamilyTreeResponse.model_validate(res.model_dump())


@router.delete(
    "/{tree_id}",
    response_model=ResultResponse,
    dependencies=[Depends(RequirePermission(Permissions.TREE_DELETE))],
)
async def delete_family_tree(
    tree_id: UUID,
    current_user: User = Depends(get_current_user),
    uow=Depends(get_uow),
) -> ResultResponse:
    usecase = DeleteFamilyTreeUseCase(uow)
    await usecase.execute(tree_id=tree_id, user_id=current_user.safe_id)
    return ResultResponse(result="ok")


@router.get(
    "/{tree_id}/members",
    response_model=list[TreeMembershipResponse],
    dependencies=[Depends(RequirePermission(Permissions.TREE_READ))],
)
async def list_tree_members(
    tree_id: UUID,
    current_user: User = Depends(get_current_user),
    uow=Depends(get_uow),
) -> list[TreeMembershipResponse]:
    usecase = ListTreeMembersUseCase(uow)
    res = await usecase.execute(tree_id=tree_id, user_id=current_user.safe_id)
    return [TreeMembershipResponse.model_validate(item.model_dump()) for item in res]


@router.post(
    "/{tree_id}/members",
    response_model=TreeMembershipResponse,
    dependencies=[Depends(require_tree_member_add)],
    status_code=201,
)
async def add_tree_member(
    tree_id: UUID,
    data: TreeMemberAddRequest,
    current_user: User = Depends(get_current_user),
    uow=Depends(get_uow),
) -> TreeMembershipResponse:
    usecase = AddTreeMemberUseCase(uow)
    res = await usecase.execute(
        tree_id=tree_id,
        actor_user_id=current_user.safe_id,
        dto=TreeMemberAddDTO(
            username=data.username,
            permissions=data.permissions,
        ),
    )
    return TreeMembershipResponse.model_validate(res.model_dump())


@router.patch(
    "/{tree_id}/members/{user_id}",
    response_model=TreeMembershipResponse,
    dependencies=[Depends(require_tree_member_add)],
)
async def update_tree_member(
    tree_id: UUID,
    user_id: UUID,
    data: TreeMemberUpdateRequest,
    current_user: User = Depends(get_current_user),
    uow=Depends(get_uow),
) -> TreeMembershipResponse:
    usecase = UpdateTreeMemberUseCase(uow)
    res = await usecase.execute(
        tree_id=tree_id,
        actor_user_id=current_user.safe_id,
        target_user_id=user_id,
        dto=TreeMemberUpdateDTO(permissions=data.permissions),
    )
    return TreeMembershipResponse.model_validate(res.model_dump())


@router.delete(
    "/{tree_id}/members/{user_id}",
    response_model=ResultResponse,
    dependencies=[Depends(require_tree_member_remove)],
)
async def remove_tree_member(
    tree_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    uow=Depends(get_uow),
) -> ResultResponse:
    usecase = RemoveTreeMemberUseCase(uow)
    await usecase.execute(
        tree_id=tree_id,
        actor_user_id=current_user.safe_id,
        target_user_id=user_id,
    )
    return ResultResponse(result="ok")
