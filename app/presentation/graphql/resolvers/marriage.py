from uuid import UUID

from strawberry.types import Info

from app.application.dto.marriage.marriage_update_dto import MarriageUpdateDTO
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
from app.domain.shared.permissions import Permissions
from app.presentation.graphql.tree_access import require_tree_member_with_access
from app.presentation.graphql.types.common import (
    ResultType,
    marriage_sort_field,
    pagination_dict,
    to_sort_order,
)
from app.presentation.graphql.types.marriage import (
    DivorceInput,
    MarriageCreateInput,
    MarriageListInput,
    MarriagePage,
    MarriageType,
    MarriageUpdateInput,
    marriage_from_mapping,
)
from app.presentation.rest.schemas.dto.common import (
    PaginationRequestParams,
    RangeRequest,
    SortRequestParams,
)
from app.presentation.rest.schemas.dto.marriage_schema import (
    DivorceRequest,
    FilterMarriageRequest,
    MarriageCreateRequest,
    MarriageFilterRequestData,
)
from app.presentation.rest.schemas.mappers.common_mappers import CommonApiMapper
from app.presentation.rest.schemas.mappers.marriage_mappers import MarriageApiMapper


async def _require_tree_member(info: Info, tree_id: UUID, permission: str):
    return await require_tree_member_with_access(info, tree_id, permission)


def _marriage_create_request(data: MarriageCreateInput) -> MarriageCreateRequest:
    return MarriageCreateRequest(
        spouse_a_id=data.spouse_a_id,
        spouse_b_id=data.spouse_b_id,
        married_at=data.married_at,
    )


def _marriage_update_dto(data: MarriageUpdateInput) -> MarriageUpdateDTO:
    raw: dict = {}
    if data.data.spouse_a_id is not None:
        raw["spouse_a_id"] = data.data.spouse_a_id
    if data.data.spouse_b_id is not None:
        raw["spouse_b_id"] = data.data.spouse_b_id
    if data.data.married_at is not None:
        raw["married_at"] = data.data.married_at
    if data.data.divorced_at is not None:
        raw["divorced_at"] = data.data.divorced_at
    return MarriageUpdateDTO.model_validate(
        {"data": raw, "where": {"marriage_id": data.where.marriage_id}}
    )


def _marriage_list_request(data: MarriageListInput | None) -> FilterMarriageRequest:
    payload = data or MarriageListInput()
    filters = None
    if payload.filters is not None:
        f = payload.filters
        married_at = None
        divorced_at = None
        if f.married_at is not None:
            married_at = RangeRequest(min=f.married_at.min, max=f.married_at.max)
        if f.divorced_at is not None:
            divorced_at = RangeRequest(min=f.divorced_at.min, max=f.divorced_at.max)
        filters = MarriageFilterRequestData(
            id=f.id,
            spouse_a_id=f.spouse_a_id,
            spouse_b_id=f.spouse_b_id,
            married_at=married_at,
            divorced_at=divorced_at,
        )
    return FilterMarriageRequest(
        pagination=PaginationRequestParams(**pagination_dict(payload.pagination)),
        filters=filters,
        sort=SortRequestParams(
            sort_order=to_sort_order(payload.sort_order),
            sort_by=marriage_sort_field(payload.sort_by),
        ),
    )


async def resolve_create_marriage(
    info: Info, tree_id: UUID, data: MarriageCreateInput
) -> MarriageType:
    await _require_tree_member(info, tree_id, Permissions.MARRIAGE_CREATE)
    usecase = CreateMarriageUseCase(
        info.context.uow, info.context.marriage_rule_service
    )
    res = await usecase.execute(
        MarriageApiMapper.to_create_marriage_dto(_marriage_create_request(data)),
        tree_id=tree_id,
    )
    mapped = MarriageApiMapper.from_create_marriage_dto(res)
    return marriage_from_mapping(mapped.model_dump())


async def resolve_update_marriage(
    info: Info, tree_id: UUID, data: MarriageUpdateInput
) -> MarriageType:
    await _require_tree_member(info, tree_id, Permissions.MARRIAGE_UPDATE)
    usecase = UpdateMarriageUseCase(
        info.context.uow, info.context.marriage_rule_service
    )
    res = await usecase.execute(_marriage_update_dto(data), tree_id=tree_id)
    mapped = MarriageApiMapper.from_update_marriage_dto(res)
    return marriage_from_mapping(mapped.model_dump())


async def resolve_delete_marriage(
    info: Info, tree_id: UUID, marriage_id: UUID
) -> ResultType:
    await _require_tree_member(info, tree_id, Permissions.MARRIAGE_DELETE)
    usecase = DeleteMarriageUseCase(info.context.uow)
    res = await usecase.execute(
        CommonApiMapper.to_id_dto(id=marriage_id), tree_id=tree_id
    )
    mapped = CommonApiMapper.from_result_dto(res)
    return ResultType(result=mapped.result)


async def resolve_divorce(info: Info, tree_id: UUID, data: DivorceInput) -> ResultType:
    await _require_tree_member(info, tree_id, Permissions.MARRIAGE_DIVORCE)
    usecase = DivorceUseCase(info.context.uow)
    req = DivorceRequest(marriage_id=data.marriage_id, divorced_at=data.divorced_at)
    res = await usecase.execute(
        MarriageApiMapper.to_add_divorce_dto(req), tree_id=tree_id
    )
    mapped = CommonApiMapper.from_result_dto(res)
    return ResultType(result=mapped.result)


async def resolve_marriage(
    info: Info, tree_id: UUID, marriage_id: UUID
) -> MarriageType:
    await _require_tree_member(info, tree_id, Permissions.MARRIAGE_READ)
    usecase = GetMarriageUseCase(info.context.uow)
    res = await usecase.execute(
        CommonApiMapper.to_id_dto(id=marriage_id), tree_id=tree_id
    )
    mapped = MarriageApiMapper.from_get_marriage_dto(res)
    return marriage_from_mapping(mapped.model_dump())


async def resolve_marriages(
    info: Info, tree_id: UUID, data: MarriageListInput | None = None
) -> MarriagePage:
    await _require_tree_member(info, tree_id, Permissions.MARRIAGE_READ)
    usecase = GetMarriageListByFilterUseCase(info.context.uow)
    res = await usecase.execute(
        MarriageApiMapper.to_get_list_marriage_dto(_marriage_list_request(data)),
        tree_id=tree_id,
    )
    mapped = MarriageApiMapper.from_get_list_marriage_dto(res)
    return MarriagePage(
        items=[marriage_from_mapping(item.model_dump()) for item in mapped.items],
        total=mapped.total,
        page=mapped.page,
        page_size=mapped.page_size,
    )
