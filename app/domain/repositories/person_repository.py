from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.person import Person
from app.domain.exceptions.person_exceptions import PersonNotFoundException
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.person_filter_dto import FilterPersonQuery


class PersonRepository(ABC):
    """
    Repository contract for Person persistence.

    This interface defines the operations required for working with
    Person entities. The actual implementation is provided in the
    infrastructure layer.
    """

    @abstractmethod
    async def create(self, person: Person) -> Person: ...

    @abstractmethod
    async def get(self, person_id: UUID) -> Person | None: ...

    @abstractmethod
    async def get_by_name(
        self, name: str, marriage_id: UUID | None, tree_id: UUID
    ) -> Person | None: ...

    async def get_in_tree_or_raise(self, person_id: UUID, tree_id: UUID) -> Person:
        from app.domain.exceptions.family_tree_exceptions import (
            PersonTreeMismatchException,
        )

        person = await self.get_or_raise(person_id=person_id)
        if person.tree_id != tree_id:
            raise PersonTreeMismatchException(
                detail=[f"person_id={person_id} tree_id={tree_id}"]
            )
        return person

    @abstractmethod
    async def get_list_by_filter(
        self, query: FilterPersonQuery
    ) -> PaginatedResult[Person]: ...

    @abstractmethod
    async def get_children(self, parent_id: UUID) -> list[Person]: ...

    @abstractmethod
    async def count_in_tree(self, tree_id: UUID) -> int: ...

    @abstractmethod
    async def update(self, person: Person) -> Person: ...

    @abstractmethod
    async def delete(self, person_id: UUID) -> None: ...

    async def get_or_raise(self, person_id: UUID) -> Person:
        """
        Find a person by id or raise an exception if not found.

        Args:
            person_id:
                ID of the target person.

        Raises:
            PersonNotFoundException:
                If no person exists with this id.
        """
        person = await self.get(person_id=person_id)

        if not person:
            raise PersonNotFoundException(detail=[f"person id is {person_id}"])
        else:
            return person
