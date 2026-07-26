from uuid import UUID

from strawberry.types import Info

from app.application.dto.person.person_update_dto import PersonUpdateDTO
from app.application.use_cases.person.create_person_use_case import CreatePersonUseCase
from app.application.use_cases.person.delete_person_use_case import DeletePersonUseCase
from app.application.use_cases.person.get_closest_relationship_use_case import (
    GetClosestRelationshipUseCase,
)
from app.application.use_cases.person.get_person_list_by_filter_use_case import (
    GetPersonListByFilterUseCase,
)
from app.application.use_cases.person.get_person_use_case import GetPersonUseCase
from app.application.use_cases.person.update_person_use_case import UpdatePersonUseCase
from app.infrastructure.utils.constants.permissions import Permissions
from app.presentation.graphql.auth import require_permission
from app.presentation.graphql.types.common import (
    ResultType,
    pagination_dict,
    person_sort_field,
    to_domain_gender,
    to_sort_order,
)
from app.presentation.graphql.types.person import (
    ClosestRelationshipType,
    PersonCreateInput,
    PersonListInput,
    PersonPage,
    PersonType,
    PersonUpdateInput,
    person_from_mapping,
)
from app.presentation.rest.schemas.dto.common import (
    PaginationRequestParams,
    RangeRequest,
    SortRequestParams,
)
from app.presentation.rest.schemas.dto.person_schema import (
    FilterPersonRequest,
    PersonCreateRequest,
    PersonFilterRequestData,
)
from app.presentation.rest.schemas.mappers.common_mappers import CommonApiMapper
from app.presentation.rest.schemas.mappers.person_mappers import PersonApiMapper
from app.presentation.utils.date_convert import jalali_to_gregorian


def _optional_jalali(value: str | None):
    if value is None:
        return None
    return jalali_to_gregorian(value)


def _person_create_request(data: PersonCreateInput) -> PersonCreateRequest:
    # model_validate keeps Jalali string date parsing aligned with REST.
    return PersonCreateRequest.model_validate(
        {
            "name": data.name,
            "gender": to_domain_gender(data.gender),
            "birth_date": data.birth_date,
            "death_date": data.death_date,
            "father_id": data.father_id,
            "mother_id": data.mother_id,
        }
    )


def _person_update_dto(data: PersonUpdateInput) -> PersonUpdateDTO:
    raw: dict = {}
    if data.data.name is not None:
        raw["name"] = data.data.name
    if data.data.gender is not None:
        raw["gender"] = to_domain_gender(data.data.gender)
    if data.data.birth_date is not None:
        raw["birth_date"] = data.data.birth_date
    if data.data.death_date is not None:
        raw["death_date"] = data.data.death_date
    if data.data.father_id is not None:
        raw["father_id"] = data.data.father_id
    if data.data.mother_id is not None:
        raw["mother_id"] = data.data.mother_id
    return PersonUpdateDTO.model_validate(
        {"data": raw, "where": {"person_id": data.where.person_id}}
    )


def _person_list_request(data: PersonListInput | None) -> FilterPersonRequest:
    payload = data or PersonListInput()
    filters = None
    if payload.filters is not None:
        f = payload.filters
        birth = None
        if f.birth_date is not None:
            birth = RangeRequest(
                min=_optional_jalali(f.birth_date.min),
                max=_optional_jalali(f.birth_date.max),
            )
        filters = PersonFilterRequestData(
            id=f.id,
            name=f.name,
            gender=to_domain_gender(f.gender) if f.gender is not None else None,
            birth_date=birth,
            father_id=f.father_id,
            mother_id=f.mother_id,
        )
    return FilterPersonRequest(
        pagination=PaginationRequestParams(**pagination_dict(payload.pagination)),
        filters=filters,
        sort=SortRequestParams(
            sort_order=to_sort_order(payload.sort_order),
            sort_by=person_sort_field(payload.sort_by),
        ),
    )


async def resolve_create_person(info: Info, data: PersonCreateInput) -> PersonType:
    await require_permission(info, Permissions.PERSON_CREATE)
    usecase = CreatePersonUseCase(info.context.uow)
    res = await usecase.execute(
        PersonApiMapper.to_create_person_dto(_person_create_request(data))
    )
    mapped = PersonApiMapper.from_create_person_dto(res)
    return person_from_mapping(mapped.model_dump())


async def resolve_update_person(info: Info, data: PersonUpdateInput) -> PersonType:
    await require_permission(info, Permissions.PERSON_UPDATE)
    usecase = UpdatePersonUseCase(info.context.uow)
    res = await usecase.execute(_person_update_dto(data))
    mapped = PersonApiMapper.from_update_person_dto(res)
    return person_from_mapping(mapped.model_dump())


async def resolve_delete_person(info: Info, person_id: UUID) -> ResultType:
    await require_permission(info, Permissions.PERSON_DELETE)
    usecase = DeletePersonUseCase(info.context.uow)
    res = await usecase.execute(CommonApiMapper.to_id_dto(person_id))
    mapped = CommonApiMapper.from_result_dto(res)
    return ResultType(result=mapped.result)


async def resolve_person(info: Info, person_id: UUID) -> PersonType:
    await require_permission(info, Permissions.PERSON_READ)
    usecase = GetPersonUseCase(info.context.uow)
    res = await usecase.execute(CommonApiMapper.to_id_dto(person_id))
    mapped = PersonApiMapper.from_get_person_dto(res)
    return person_from_mapping(mapped.model_dump())


async def resolve_persons(
    info: Info, data: PersonListInput | None = None
) -> PersonPage:
    await require_permission(info, Permissions.PERSON_READ)
    usecase = GetPersonListByFilterUseCase(info.context.uow)
    res = await usecase.execute(
        PersonApiMapper.to_get_list_person_dto(_person_list_request(data))
    )
    mapped = PersonApiMapper.from_get_list_person_dto(res)
    return PersonPage(
        items=[person_from_mapping(item.model_dump()) for item in mapped.items],
        total=mapped.total,
        page=mapped.page,
        page_size=mapped.page_size,
    )


async def resolve_closest_relationship(
    info: Info,
    from_person_id: UUID,
    to_person_id: UUID,
) -> ClosestRelationshipType:
    await require_permission(info, Permissions.PERSON_READ)
    usecase = GetClosestRelationshipUseCase(info.context.neo)
    result = usecase.execute(from_person_id, to_person_id)
    data = result.model_dump()
    return ClosestRelationshipType(
        from_person_id=data["from_person_id"],
        to_person_id=data["to_person_id"],
        found=data["found"],
        distance=data.get("distance"),
        path_person_ids=list(data.get("path_person_ids") or []),
        relationship_types=list(data.get("relationship_types") or []),
    )
