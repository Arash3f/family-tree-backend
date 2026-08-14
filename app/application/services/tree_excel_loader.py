from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.marriage import Marriage
from app.domain.entities.person import Person
from app.domain.shared.dto.marriage_filter_dto import (
    FilterMarriageDTO,
    MarriageFilterDataDTO,
    MarriageSortField,
)
from app.domain.shared.dto.pagination_dto import PaginationParams
from app.domain.shared.dto.person_filter_dto import (
    FilterPersonQuery,
    PersonFilterDTO,
    PersonSortField,
)
from app.domain.shared.dto.sorter_dto import SortOrderField, SortParams

_PAGE_SIZE = 100


async def load_all_tree_persons(uow: UnitOfWork, tree_id: UUID) -> list[Person]:
    items: list[Person] = []
    page = 1
    while True:
        result = await uow.persons.get_list_by_filter(
            query=FilterPersonQuery(
                pagination=PaginationParams(page=page, page_size=_PAGE_SIZE, offset=0),
                filters=PersonFilterDTO(tree_id=tree_id),
                sort=SortParams(
                    sort_order=SortOrderField.ASC,
                    sort_by=PersonSortField.NAME,
                ),
            )
        )
        items.extend(result.items)
        if len(items) >= result.total or not result.items:
            break
        page += 1
    return items


async def load_all_tree_marriages(uow: UnitOfWork, tree_id: UUID) -> list[Marriage]:
    items: list[Marriage] = []
    page = 1
    while True:
        result = await uow.marriages.get_list_by_filter(
            query=FilterMarriageDTO(
                pagination=PaginationParams(page=page, page_size=_PAGE_SIZE, offset=0),
                filters=MarriageFilterDataDTO(tree_id=tree_id),
                sort=SortParams(
                    sort_order=SortOrderField.ASC,
                    sort_by=MarriageSortField.ID,
                ),
            )
        )
        items.extend(result.items)
        if len(items) >= result.total or not result.items:
            break
        page += 1
    return items
