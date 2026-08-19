from uuid import UUID

from fastapi import APIRouter, Depends

from app.application.services.person_photo_service import PersonPhotoService
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
from app.domain.entities.family_tree import TreeMembership
from app.presentation.dependencies import (
    get_neo,
    get_person_photo_service,
    get_request_uow,
)
from app.presentation.rest.dependencies.tree_guard import (
    require_tree_person_create,
    require_tree_person_delete,
    require_tree_person_update,
    require_tree_view,
)
from app.presentation.rest.schemas.dto.common import PaginatedResponse, ResultResponse
from app.presentation.rest.schemas.dto.person_schema import (
    ClosestRelationshipResponse,
    FilterPersonRequest,
    PersonCreateRequest,
    PersonCreateResponse,
    PersonGetResponse,
    PersonModel,
    PersonUpdateRequest,
    PersonUpdateResponse,
)
from app.presentation.rest.schemas.mappers.common_mappers import CommonApiMapper
from app.presentation.rest.schemas.mappers.person_mappers import PersonApiMapper
from app.presentation.tree_data_access import redact_person_data

router = APIRouter(prefix="/persons", tags=["Persons"])


@router.post(
    "",
    response_model=PersonCreateResponse,
)
async def create_person(
    tree_id: UUID,
    data: PersonCreateRequest,
    membership: TreeMembership = Depends(require_tree_person_create),
    uow=Depends(get_request_uow),
    photo_service: PersonPhotoService = Depends(get_person_photo_service),
) -> PersonCreateResponse:
    usecase = CreatePersonUseCase(uow, photo_service)
    res = await usecase.execute(
        PersonApiMapper.to_create_person_dto(data), tree_id=tree_id
    )
    response = PersonApiMapper.from_create_person_dto(res)
    return PersonCreateResponse.model_validate(
        redact_person_data(response.model_dump(), membership)
    )


@router.delete(
    "/{person_id}",
    response_model=ResultResponse,
    dependencies=[Depends(require_tree_person_delete)],
)
async def delete_person(
    tree_id: UUID,
    person_id: UUID,
    uow=Depends(get_request_uow),
    photo_service: PersonPhotoService = Depends(get_person_photo_service),
) -> ResultResponse:
    usecase = DeletePersonUseCase(uow, photo_service)
    res = await usecase.execute(CommonApiMapper.to_id_dto(person_id), tree_id=tree_id)
    return CommonApiMapper.from_result_dto(res)


@router.put(
    "",
    response_model=PersonUpdateResponse,
)
async def update_person(
    tree_id: UUID,
    data: PersonUpdateRequest,
    membership: TreeMembership = Depends(require_tree_person_update),
    uow=Depends(get_request_uow),
    photo_service: PersonPhotoService = Depends(get_person_photo_service),
) -> PersonUpdateResponse:
    usecase = UpdatePersonUseCase(uow, photo_service)
    res = await usecase.execute(
        PersonApiMapper.to_update_person_dto(data), tree_id=tree_id
    )
    response = PersonApiMapper.from_update_person_dto(res)
    return PersonUpdateResponse.model_validate(
        redact_person_data(response.model_dump(), membership)
    )


@router.get(
    "/{from_person_id}/relation/{to_person_id}",
    response_model=ClosestRelationshipResponse,
    dependencies=[Depends(require_tree_view)],
)
async def get_closest_relationship(
    tree_id: UUID,
    from_person_id: UUID,
    to_person_id: UUID,
    neo=Depends(get_neo),
    uow=Depends(get_request_uow),
) -> ClosestRelationshipResponse:
    usecase = GetClosestRelationshipUseCase(neo, uow)
    result = await usecase.execute(from_person_id, to_person_id, tree_id=tree_id)
    return ClosestRelationshipResponse.model_validate(result.model_dump())


@router.get(
    "/{person_id}",
    response_model=PersonGetResponse,
)
async def get_person(
    tree_id: UUID,
    person_id: UUID,
    membership: TreeMembership = Depends(require_tree_view),
    uow=Depends(get_request_uow),
    photo_service: PersonPhotoService = Depends(get_person_photo_service),
) -> PersonGetResponse:
    usecase = GetPersonUseCase(uow, photo_service)
    res = await usecase.execute(CommonApiMapper.to_id_dto(person_id), tree_id=tree_id)
    response = PersonApiMapper.from_get_person_dto(res)
    return PersonGetResponse.model_validate(
        redact_person_data(response.model_dump(), membership)
    )


@router.post(
    "/list",
    response_model=PaginatedResponse[PersonModel],
)
async def get_person_list_by_filter(
    tree_id: UUID,
    data: FilterPersonRequest,
    membership: TreeMembership = Depends(require_tree_view),
    uow=Depends(get_request_uow),
    photo_service: PersonPhotoService = Depends(get_person_photo_service),
) -> PaginatedResponse[PersonModel]:
    usecase = GetPersonListByFilterUseCase(uow, photo_service)
    res = await usecase.execute(
        PersonApiMapper.to_get_list_person_dto(data), tree_id=tree_id
    )
    response = PersonApiMapper.from_get_list_person_dto(res)
    return response.model_copy(
        update={
            "items": [
                PersonModel.model_validate(
                    redact_person_data(item.model_dump(), membership)
                )
                for item in response.items
            ]
        }
    )
