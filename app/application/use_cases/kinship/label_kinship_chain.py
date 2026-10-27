from app.application.dto.kinship_dto import KinshipChainDTO, KinshipLabelDTO
from app.domain.services.kinship_chain import label_kinship_chain


class LabelKinshipChainUseCase:
    """Name a relation given as a chain of family steps; reads no data."""

    def execute(self, dto: KinshipChainDTO) -> KinshipLabelDTO:
        labels = label_kinship_chain(dto.steps)
        return KinshipLabelDTO(
            label_fa=labels.label_fa,
            label_en=labels.label_en,
            description_fa=labels.description_fa,
            description_en=labels.description_en,
        )
