from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.shared.dto.common_dto import IdDTO, ResultDTO


class DeleteUserUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: IdDTO) -> ResultDTO:
        async with self.uow:
            user = await self.uow.users.get_or_raise(user_id=dto.id)

            user.is_active = False
            await self.uow.users.update(user)

            # Trees this user owns: detach every member (including the owner).
            owned_trees = await self.uow.family_trees.list_owned_by_user(user.safe_id)
            for tree in owned_trees:
                await self.uow.tree_memberships.delete_all_for_tree(tree.safe_id)

            # Trees they only joined: remove their membership.
            await self.uow.tree_memberships.delete_all_for_user(user.safe_id)

            await self.uow.commit()

            return ResultDTO(result="User deleted successfully")
