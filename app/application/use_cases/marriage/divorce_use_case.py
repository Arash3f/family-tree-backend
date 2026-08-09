from uuid import UUID

from app.application.dto.marriage.divorce_dto import DivorceDTO
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.family_tree_sync_service import FamilyTreeSyncService
from app.domain.shared.dto.common_dto import ResultDTO


class DivorceUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        sync_service: FamilyTreeSyncService | None = None,
    ):
        self.uow = uow
        self.sync_service = sync_service or FamilyTreeSyncService()

    async def execute(self, dto: DivorceDTO, *, tree_id: UUID) -> ResultDTO:
        async with self.uow:
            marriage = await self.uow.marriages.get_in_tree_or_raise(
                marriage_id=dto.marriage_id, tree_id=tree_id
            )

            spouse_a_id = marriage.spouse_a_id
            spouse_b_id = marriage.spouse_b_id

            marriage.divorce(divorced_at=dto.divorced_at)

            await self.uow.marriages.end(
                marriage_id=marriage.safe_id, divorced_at=marriage.safe_divorced_at
            )

            await self.uow.commit()

            self.sync_service.remove_spouse(spouse_a_id, spouse_b_id)

            return ResultDTO(result="Divorce recorded successfully")
