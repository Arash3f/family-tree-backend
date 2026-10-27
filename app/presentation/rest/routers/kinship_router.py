from fastapi import APIRouter, Depends

from app.application.dto.kinship_dto import KinshipChainDTO
from app.application.use_cases.kinship.label_kinship_chain import (
    LabelKinshipChainUseCase,
)
from app.presentation.rest.dependencies.rate_limit import rate_limit_kinship
from app.presentation.rest.schemas.dto.kinship_schema import (
    KinshipLabelRequest,
    KinshipLabelResponse,
)

router = APIRouter(prefix="/kinship", tags=["Kinship"])


@router.post(
    "/label",
    response_model=KinshipLabelResponse,
    dependencies=[Depends(rate_limit_kinship)],
    summary="Name a relation given as a chain of family steps",
    description=(
        "Public and stateless: no account, no tree, nothing stored. Uses the "
        "same labeller as the relationship finder, so the names match the app."
    ),
)
async def label_kinship_chain(data: KinshipLabelRequest) -> KinshipLabelResponse:
    result = LabelKinshipChainUseCase().execute(KinshipChainDTO(steps=data.steps))
    return KinshipLabelResponse.model_validate(result.model_dump())
