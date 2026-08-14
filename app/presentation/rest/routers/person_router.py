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
from app.domain.shared.permissions import Permissions
from app.presentation.rest.dependencies.permission_guard import RequirePermission
from app.presentation.rest.dependencies.tree_guard import (
    require_tree_add_persons,
    require_tree_edit,
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
from app.presentation.rest.utils.dependencies import (
    get_neo,
    get_person_photo_service,
    get_uow,
)

router = APIRouter(prefix="/persons", tags=["Persons"])


@router.post(
    "",
    response_model=PersonCreateResponse,
    dependencies=[
        Depends(RequirePermission(Permissions.PERSON_CREATE)),
        Depends(require_tree_add_persons),
    ],
)
async def create_person(
    tree_id: UUID,
    data: PersonCreateRequest,
    uow=Depends(get_uow),
    photo_service: PersonPhotoService = Depends(get_person_photo_service),
) -> PersonCreateResponse:
    usecase = CreatePersonUseCase(uow, photo_service)
    res = await usecase.execute(
        PersonApiMapper.to_create_person_dto(data), tree_id=tree_id
    )
    return PersonApiMapper.from_create_person_dto(res)


@router.delete(
    "/{person_id}",
    response_model=ResultResponse,
    dependencies=[
        Depends(RequirePermission(Permissions.PERSON_DELETE)),
        Depends(require_tree_edit),
    ],
)
async def delete_person(
    tree_id: UUID,
    person_id: UUID,
    uow=Depends(get_uow),
    photo_service: PersonPhotoService = Depends(get_person_photo_service),
) -> ResultResponse:
    usecase = DeletePersonUseCase(uow, photo_service)
    res = await usecase.execute(CommonApiMapper.to_id_dto(person_id), tree_id=tree_id)
    return CommonApiMapper.from_result_dto(res)


@router.put(
    "",
    response_model=PersonUpdateResponse,
    dependencies=[
        Depends(RequirePermission(Permissions.PERSON_UPDATE)),
        Depends(require_tree_edit),
    ],
)
async def update_person(
    tree_id: UUID,
    data: PersonUpdateRequest,
    uow=Depends(get_uow),
    photo_service: PersonPhotoService = Depends(get_person_photo_service),
) -> PersonUpdateResponse:
    usecase = UpdatePersonUseCase(uow, photo_service)
    res = await usecase.execute(
        PersonApiMapper.to_update_person_dto(data), tree_id=tree_id
    )
    return PersonApiMapper.from_update_person_dto(res)


@router.get(
    "/{from_person_id}/relation/{to_person_id}",
    response_model=ClosestRelationshipResponse,
    dependencies=[
        Depends(RequirePermission(Permissions.PERSON_READ)),
        Depends(require_tree_view),
    ],
)
async def get_closest_relationship(
    tree_id: UUID,
    from_person_id: UUID,
    to_person_id: UUID,
    neo=Depends(get_neo),
    uow=Depends(get_uow),
) -> ClosestRelationshipResponse:
    usecase = GetClosestRelationshipUseCase(neo, uow)
    result = await usecase.execute(from_person_id, to_person_id, tree_id=tree_id)
    return ClosestRelationshipResponse.model_validate(result.model_dump())


@router.get(
    "/{person_id}",
    response_model=PersonGetResponse,
    dependencies=[
        Depends(RequirePermission(Permissions.PERSON_READ)),
        Depends(require_tree_view),
    ],
)
async def get_person(
    tree_id: UUID,
    person_id: UUID,
    uow=Depends(get_uow),
    photo_service: PersonPhotoService = Depends(get_person_photo_service),
) -> PersonGetResponse:
    usecase = GetPersonUseCase(uow, photo_service)
    res = await usecase.execute(CommonApiMapper.to_id_dto(person_id), tree_id=tree_id)
    return PersonApiMapper.from_get_person_dto(res)


@router.post(
    "/list",
    response_model=PaginatedResponse[PersonModel],
    dependencies=[
        Depends(RequirePermission(Permissions.PERSON_READ)),
        Depends(require_tree_view),
    ],
)
async def get_person_list_by_filter(
    tree_id: UUID,
    data: FilterPersonRequest,
    uow=Depends(get_uow),
    photo_service: PersonPhotoService = Depends(get_person_photo_service),
) -> PaginatedResponse[PersonModel]:
    usecase = GetPersonListByFilterUseCase(uow, photo_service)
    res = await usecase.execute(
        PersonApiMapper.to_get_list_person_dto(data), tree_id=tree_id
    )
    return PersonApiMapper.from_get_list_person_dto(res)
