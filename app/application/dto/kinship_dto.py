from pydantic import BaseModel, Field

from app.domain.services.kinship_chain import MAX_KINSHIP_STEPS, KinshipStep


class KinshipChainDTO(BaseModel):
    steps: list[KinshipStep] = Field(min_length=1, max_length=MAX_KINSHIP_STEPS)


class KinshipLabelDTO(BaseModel):
    label_fa: str | None
    label_en: str | None
    description_fa: str | None
    description_en: str | None
