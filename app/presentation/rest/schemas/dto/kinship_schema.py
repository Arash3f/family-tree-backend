from pydantic import BaseModel, Field

from app.domain.services.kinship_chain import MAX_KINSHIP_STEPS, KinshipStep


class KinshipLabelRequest(BaseModel):
    steps: list[KinshipStep] = Field(
        min_length=1,
        max_length=MAX_KINSHIP_STEPS,
        description=(
            "The chain from the speaker outwards: "
            '["father", "brother", "son"] is "my father\'s brother\'s son".'
        ),
    )


class KinshipLabelResponse(BaseModel):
    label_fa: str | None = Field(description="The relation's Persian name, e.g. پسرعمو")
    label_en: str | None = Field(
        description="The English name, e.g. paternal uncle's son"
    )
    description_fa: str | None = Field(description="The chain word by word, in Persian")
    description_en: str | None = Field(description="The chain word by word, in English")
