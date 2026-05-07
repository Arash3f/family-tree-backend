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
from app.domain.constants.permissions import Permissions
from app.presentation.rest.dependencies.permission_guard import RequirePermission
from app.presentation.rest.utils.dependencies import get_marriage_rule_service, get_uow
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
from app.presentation.rest.schemas.mappers.comman_mappers import CommonApiMapper
from app.presentation.rest.schemas.mappers.marriage_mappers import MarriageApiMapper

router = APIRouter(prefix="/marriages", tags=["Marriages"])


@router.post(
    "/",
    response_model=MarriageGetResponse,
    dependencies=[Depends(RequirePermission(Permissions.MARRIAGE_CREATE))],
)
async def create_marriage(
    data: MarriageCreateRequest,
    uow=Depends(get_uow),
) -> MarriageCreateResponse:
    usecase = CreateMarriageUseCase(uow)

    res = await usecase.execute(MarriageApiMapper.to_create_marriage_dto(data))

    return MarriageApiMapper.from_create_marriage_dto(res)


@router.delete(
    "/",
    response_model=ResultResponse,
    dependencies=[Depends(RequirePermission(Permissions.MARRIAGE_DELETE))],
)
async def delete_marriage(
    data: IdRequest,
    uow=Depends(get_uow),
) -> ResultResponse:
    usecase = DeleteMarriageUseCase(uow)

    res = await usecase.execute(CommonApiMapper.to_id_dto(id=data.id))

    return CommonApiMapper.from_result_dto(res)


@router.put(
    "/",
    response_model=MarriageUpdateResponse,
    dependencies=[Depends(RequirePermission(Permissions.MARRIAGE_UPDATE))],
)
async def update_marriage(
    data: MarriageUpdateRequest,
    uow=Depends(get_uow),
    marriage_rule_service=Depends(get_marriage_rule_service),
) -> MarriageUpdateResponse:
    usecase = UpdateMarriageUseCase(uow, marriage_rule_service)

    res = await usecase.execute(MarriageApiMapper.to_update_marriage_dto(data))

    return MarriageApiMapper.from_update_marriage_dto(res)


@router.get(
    "/{marriage_id}",
    response_model=MarriageGetResponse,
    dependencies=[Depends(RequirePermission(Permissions.MARRIAGE_READ))],
)
async def get_marriage(
    marriage_id: int,
    uow=Depends(get_uow),
) -> MarriageGetResponse:
    usecase = GetMarriageUseCase(uow)

    res = await usecase.execute(CommonApiMapper.to_id_dto(id=marriage_id))

    return MarriageApiMapper.from_get_marriage_dto(res)


@router.get(
    "/list",
    response_model=PaginatedResponse[MarriageModel],
    dependencies=[Depends(RequirePermission(Permissions.MARRIAGE_READ))],
)
async def get_marriage_list_by_filter(
    data: FilterMarriageRequest,
    uow=Depends(get_uow),
) -> PaginatedResponse[MarriageModel]:
    usecase = GetMarriageListByFilterUseCase(uow)

    res = await usecase.execute(MarriageApiMapper.to_get_list_marriage_dto(data))

    return MarriageApiMapper.from_get_list_marriage_dto(res)


@router.get(
    "/divorce",
    response_model=ResultResponse,
    dependencies=[Depends(RequirePermission(Permissions.MARRIAGE_DIVORCE))],
)
async def divorce(
    data: DivorceRequest,
    uow=Depends(get_uow),
) -> ResultResponse:
    usecase = DivorceUseCase(uow)

    res = await usecase.execute(MarriageApiMapper.to_add_divorce_dto(data))

    return CommonApiMapper.from_result_dto(res)
