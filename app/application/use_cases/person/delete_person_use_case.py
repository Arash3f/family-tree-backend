from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.family_tree_sync_service import FamilyTreeSyncService
from app.domain.exceptions.person_exceptions import PersonHasMarriagesException
from app.domain.shared.dto.common_dto import IdDTO, ResultDTO


class DeletePersonUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        sync_service: FamilyTreeSyncService | None = None,
    ):
        self.uow = uow
        self.sync_service = sync_service or FamilyTreeSyncService()

    async def execute(self, dto: IdDTO) -> ResultDTO:
        async with self.uow:
            person = await self.uow.persons.get_or_raise(person_id=dto.id)
            person_id = person.safe_id

            if await self.uow.marriages.exists_for_person(person_id):
                raise PersonHasMarriagesException(
                    detail=[f"person {person_id} is linked to one or more marriages"]
                )

            await self.uow.persons.delete(person_id=person_id)

            await self.uow.commit()

            self.sync_service.delete_person(person_id)

            return ResultDTO(result="Person deleted successfully")
