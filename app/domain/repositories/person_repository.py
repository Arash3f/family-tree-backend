from abc import ABC, abstractmethod

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
    async def get(self, person_id: int) -> Person | None: ...

    @abstractmethod
    async def get_list_by_filter(
        self, query: FilterPersonQuery
    ) -> PaginatedResult[Person]: ...

    @abstractmethod
    async def get_children(self, parent_id: int) -> list[Person]: ...

    @abstractmethod
    async def update(self, person: Person) -> Person: ...

    @abstractmethod
    async def delete(self, person_id: int) -> None: ...

    async def get_or_raise(self, person_id: int) -> Person:
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
