from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.family_tree_sync_service import FamilyTreeSyncService
from app.domain.shared.dto.common_dto import IdDTO, ResultDTO


class DeleteMarriageUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        sync_service: FamilyTreeSyncService | None = None,
    ):
        self.uow = uow
        self.sync_service = sync_service or FamilyTreeSyncService()

    async def execute(self, dto: IdDTO) -> ResultDTO:
        async with self.uow:
            marriage = await self.uow.marriages.get_or_raise(marriage_id=dto.id)
            husband_id = marriage.husband_id
            wife_id = marriage.wife_id

            await self.uow.marriages.delete(marriage_id=marriage.safe_id)

            await self.uow.commit()

            self.sync_service.remove_spouse(husband_id, wife_id)

            return ResultDTO(result="Marriage deleted successfully")
