from fastapi import APIRouter, Depends

from app.application.use_cases.person.create_person_use_case import CreatePersonUseCase
from app.application.use_cases.person.delete_person_use_case import DeletePersonUseCase
from app.application.use_cases.person.get_person_list_by_filter_use_case import (
    GetPersonListByFilterUseCase,
)
from app.application.use_cases.person.get_persson_use_case import GetPersonUseCase
from app.application.use_cases.person.update_person_use_case import UpdatePersonUseCase
from app.presentation.rest.dependencies import get_uow
from app.presentation.rest.errors.handlers import ErrorResponse
from app.presentation.rest.schemas.dto.common import PaginatedResponse, ResultResponse
from app.presentation.rest.schemas.dto.person_schema import (
    FilterPersonRequest,
    PersonCreateRequest,
    PersonCreateResponse,
    PersonGetResponse,
    PersonModel,
    PersonUpdateRequest,
    PersonUpdateResponse,
)
from app.presentation.rest.schemas.mappers.comman_mappers import CommonApiMapper
from app.presentation.rest.schemas.mappers.person_mappers import PersonApiMapper

router = APIRouter(prefix="/persons", tags=["Persons"])


@router.post(
    "/",
    summary="Create a new person",
    description="Creates a new person in the system and returns the created record.",
    response_model=PersonCreateResponse,
    status_code=201,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Bad request"},
    },
)
async def create_person(
    data: PersonCreateRequest,
    uow=Depends(get_uow),
) -> PersonCreateResponse:
    usecase = CreatePersonUseCase(uow)

    res = await usecase.execute(PersonApiMapper.to_create_person_dto(data))

    return PersonApiMapper.from_create_person_dto(res)


@router.delete("/{person_id}", response_model=ResultResponse)
async def delete_person(
    person_id: int,
    uow=Depends(get_uow),
) -> ResultResponse:
    usecase = DeletePersonUseCase(uow)

    res = await usecase.execute(CommonApiMapper.to_id_dto(person_id))

    return CommonApiMapper.from_result_dto(res)


@router.put("/", response_model=PersonUpdateResponse)
async def update_person(
    data: PersonUpdateRequest,
    uow=Depends(get_uow),
) -> PersonUpdateResponse:
    usecase = UpdatePersonUseCase(uow)

    res = await usecase.execute(PersonApiMapper.to_update_person_dto(data))

    return PersonApiMapper.from_update_person_dto(res)


@router.get("/{person_id}", response_model=PersonGetResponse)
async def get_person(
    person_id: int,
    uow=Depends(get_uow),
) -> PersonGetResponse:
    usecase = GetPersonUseCase(uow)

    res = await usecase.execute(CommonApiMapper.to_id_dto(person_id))

    return PersonApiMapper.from_get_person_dto(res)


@router.post("/list/", response_model=PaginatedResponse[PersonModel])
async def get_person_list_by_filter(
    data: FilterPersonRequest,
    uow=Depends(get_uow),
) -> PaginatedResponse[PersonModel]:
    usecase = GetPersonListByFilterUseCase(uow)

    res = await usecase.execute(PersonApiMapper.to_get_list_person_dto(data))

    return PersonApiMapper.from_get_list_person_dto(res)
