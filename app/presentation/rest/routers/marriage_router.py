from uuid import UUID

from fastapi import APIRouter, Depends

from app.application.use_cases.marriage.create_marriage_use_case import (
    CreateMarriageUseCase,
)
from app.application.use_cases.marriage.delete_marriage_use_case import (
    DeleteMarriageUseCase,
)
from app.application.use_cases.marriage.divorce_use_case import DivorceUseCase
from app.application.use_cases.marriage.get_marriage_list_by_filter_use_case import (
    GetMarriageListByFilterUseCase,
)
from app.application.use_cases.marriage.get_marriage_use_case import GetMarriageUseCase
from app.application.use_cases.marriage.update_marriage_use_case import (
    UpdateMarriageUseCase,
)
from app.domain.entities.family_tree import TreeMembership
from app.presentation.tree_data_access import redact_marriage_data
from app.presentation.rest.dependencies.tree_guard import (
    require_tree_marriage_create,
    require_tree_marriage_delete,
    require_tree_marriage_divorce,
    require_tree_marriage_update,
    require_tree_view,
)
from app.presentation.rest.schemas.dto.common import (
    IdRequest,
    PaginatedResponse,
    ResultResponse,
)
from app.presentation.rest.schemas.dto.marriage_schema import (
    DivorceRequest,
    FilterMarriageRequest,
    MarriageCreateRequest,
    MarriageCreateResponse,
    MarriageGetResponse,
    MarriageModel,
    MarriageUpdateRequest,
    MarriageUpdateResponse,
)
from app.presentation.rest.schemas.mappers.common_mappers import CommonApiMapper
from app.presentation.rest.schemas.mappers.marriage_mappers import MarriageApiMapper
from app.presentation.rest.utils.dependencies import get_marriage_rules_service, get_uow

router = APIRouter(prefix="/marriages", tags=["Marriages"])


@router.post(
    "",
    response_model=MarriageCreateResponse,
)
async def create_marriage(
    tree_id: UUID,
    data: MarriageCreateRequest,
    membership: TreeMembership = Depends(require_tree_marriage_create),
    uow=Depends(get_uow),
    marriage_rule_service=Depends(get_marriage_rules_service),
) -> MarriageCreateResponse:
    usecase = CreateMarriageUseCase(uow, marriage_rule_service)
    res = await usecase.execute(
        MarriageApiMapper.to_create_marriage_dto(data), tree_id=tree_id
    )
    response = MarriageApiMapper.from_create_marriage_dto(res)
    return MarriageCreateResponse.model_validate(
        redact_marriage_data(response.model_dump(), membership)
    )


@router.delete(
    "",
    response_model=ResultResponse,
    dependencies=[Depends(require_tree_marriage_delete)],
)
async def delete_marriage(
    tree_id: UUID,
    data: IdRequest,
    uow=Depends(get_uow),
) -> ResultResponse:
    usecase = DeleteMarriageUseCase(uow)
    res = await usecase.execute(CommonApiMapper.to_id_dto(id=data.id), tree_id=tree_id)
    return CommonApiMapper.from_result_dto(res)


@router.put(
    "",
    response_model=MarriageUpdateResponse,
)
async def update_marriage(
    tree_id: UUID,
    data: MarriageUpdateRequest,
    membership: TreeMembership = Depends(require_tree_marriage_update),
    uow=Depends(get_uow),
    marriage_rule_service=Depends(get_marriage_rules_service),
) -> MarriageUpdateResponse:
    usecase = UpdateMarriageUseCase(uow, marriage_rule_service)
    res = await usecase.execute(
        MarriageApiMapper.to_update_marriage_dto(data), tree_id=tree_id
    )
    response = MarriageApiMapper.from_update_marriage_dto(res)
    return MarriageUpdateResponse.model_validate(
        redact_marriage_data(response.model_dump(), membership)
    )


@router.post(
    "/list",
    response_model=PaginatedResponse[MarriageModel],
)
async def get_marriage_list_by_filter(
    tree_id: UUID,
    data: FilterMarriageRequest,
    membership: TreeMembership = Depends(require_tree_view),
    uow=Depends(get_uow),
) -> PaginatedResponse[MarriageModel]:
    usecase = GetMarriageListByFilterUseCase(uow)
    res = await usecase.execute(
        MarriageApiMapper.to_get_list_marriage_dto(data), tree_id=tree_id
    )
    response = MarriageApiMapper.from_get_list_marriage_dto(res)
    return response.model_copy(
        update={
            "items": [
                MarriageModel.model_validate(
                    redact_marriage_data(item.model_dump(), membership)
                )
                for item in response.items
            ]
        }
    )


@router.post(
    "/divorce",
    response_model=ResultResponse,
    dependencies=[Depends(require_tree_marriage_divorce)],
)
async def divorce(
    tree_id: UUID,
    data: DivorceRequest,
    uow=Depends(get_uow),
) -> ResultResponse:
    usecase = DivorceUseCase(uow)
    res = await usecase.execute(
        MarriageApiMapper.to_add_divorce_dto(data), tree_id=tree_id
    )
    return CommonApiMapper.from_result_dto(res)


@router.get(
    "/{marriage_id}",
    response_model=MarriageGetResponse,
)
async def get_marriage(
    tree_id: UUID,
    marriage_id: UUID,
    membership: TreeMembership = Depends(require_tree_view),
    uow=Depends(get_uow),
) -> MarriageGetResponse:
    usecase = GetMarriageUseCase(uow)
    res = await usecase.execute(
        CommonApiMapper.to_id_dto(id=marriage_id), tree_id=tree_id
    )
    response = MarriageApiMapper.from_get_marriage_dto(res)
    return MarriageGetResponse.model_validate(
        redact_marriage_data(response.model_dump(), membership)
    )
