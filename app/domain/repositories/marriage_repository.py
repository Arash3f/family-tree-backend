from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from app.domain.entities.marriage import Marriage
from app.domain.exceptions.marriage_exceptions import MarriageNotFoundException
from app.domain.shared.dto.marriage_filter_dto import FilterMarriageDTO
from app.domain.shared.dto.pagination_dto import PaginatedResult


class MarriageRepository(ABC):
    """
    Repository contract for User Marriage.

    This interface defines the operations required for working with
    User entities. The actual implementation is provided in the
    infrastructure layer.
    """

    @abstractmethod
    async def create(self, marriage: Marriage) -> Marriage: ...

    @abstractmethod
    async def end(self, marriage_id: UUID, divorced_at: date) -> None: ...

    @abstractmethod
    async def get_list_by_filter(
        self, query: FilterMarriageDTO
    ) -> PaginatedResult[Marriage]: ...

    @abstractmethod
    async def get(self, marriage_id: UUID) -> Marriage | None: ...

    @abstractmethod
    async def get_by_ids(self, spouse_a_id: UUID, spouse_b_id: UUID) -> Marriage | None: ...

    @abstractmethod
    async def has_active_for_person(
        self,
        person_id: UUID,
        exclude_marriage_id: UUID | None = None,
    ) -> bool: ...

    @abstractmethod
    async def exists_for_person(self, person_id: UUID) -> bool: ...

    @abstractmethod
    async def delete(self, marriage_id: UUID) -> None: ...

    @abstractmethod
    async def update(self, marriage: Marriage) -> Marriage: ...

    async def get_or_raise(self, marriage_id: UUID) -> Marriage:
        """
        Find a person by id or raise an exception if not found.

        Args:
            person_id:
                ID of the target person.

        Raises:
            PersonNotFoundException:
                If no person exists with this id.
        """
        marriage = await self.get(marriage_id=marriage_id)

        if not marriage:
            raise MarriageNotFoundException(detail=[f"marriage id is {marriage_id}"])
        else:
            return marriage
