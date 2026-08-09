from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.family_tree_sync_service import FamilyTreeSyncService
from app.application.services.person_photo_service import PersonPhotoService
from app.domain.exceptions.person_exceptions import (
    PersonHasChildrenException,
    PersonHasMarriagesException,
)
from app.domain.shared.dto.common_dto import IdDTO, ResultDTO


class DeletePersonUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        photo_service: PersonPhotoService,
        sync_service: FamilyTreeSyncService | None = None,
    ):
        self.uow = uow
        self.photo_service = photo_service
        self.sync_service = sync_service or FamilyTreeSyncService()

    async def execute(self, dto: IdDTO, *, tree_id: UUID) -> ResultDTO:
        async with self.uow:
            person = await self.uow.persons.get_in_tree_or_raise(
                person_id=dto.id, tree_id=tree_id
            )
            person_id = person.safe_id
            photo_key = person.photo_object_key

            # A past marriage is history worth keeping, so only a live one
            # blocks deletion.
            if await self.uow.marriages.has_active_for_person(person_id):
                raise PersonHasMarriagesException(
                    detail=[f"person {person_id} has an active marriage"]
                )

            # Deleting a parent would leave their children pointing at a person
            # that no longer resolves.
            children = await self.uow.persons.get_children(person_id)
            if children:
                raise PersonHasChildrenException(
                    detail=[
                        f"person {person_id} is a parent of {len(children)} person(s)"
                    ]
                )

            await self.uow.persons.delete(person_id=person_id)

            await self.uow.commit()

            self.sync_service.delete_person(person_id)
            await self.photo_service.delete_quiet(photo_key)

            return ResultDTO(result="Person deleted successfully")
