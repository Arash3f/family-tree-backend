from app.domain.shared.dto.common_dto import IdDTO, ResultDTO
from app.presentation.rest.schemas.dto.common import ResultResponse


class CommonApiMapper:
    @staticmethod
    def to_id_dto(id: int) -> IdDTO:
        return IdDTO(
            id=id,
        )

    @staticmethod
    def from_result_dto(response: ResultDTO) -> ResultResponse:
        return ResultResponse(result=response.result)
