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

# Map Arabic character variants to their Persian equivalents so that names
# written with different keyboards sort consistently.
_PERSIAN_NORMALIZATION = str.maketrans(
    {
        "\u064a": "\u06cc",  # Arabic yeh -> Persian yeh
        "\u0649": "\u06cc",  # Alef maksura -> Persian yeh
        "\u0643": "\u06a9",  # Arabic kaf -> Persian keheh
        "\u0629": "\u0647",  # Teh marbuta -> heh
        "\u0623": "\u0627",  # Alef with hamza above -> alef
        "\u0625": "\u0627",  # Alef with hamza below -> alef
        "\u0622": "\u0627",  # Alef with madda -> alef
        "\u200c": " ",  # ZWNJ -> space
    }
)


def _name_sort_key(person: Person) -> tuple[str, str]:
    """Build a locale-friendly key so persons are ordered by name.

    Postgres sorts Persian text by raw Unicode code points, which breaks the
    expected alphabetical order. Normalizing character variants and whitespace
    here guarantees the exported Excel is ordered by name (then family name).
    """

    def normalize(value: str | None) -> str:
        text = (value or "").translate(_PERSIAN_NORMALIZATION)
        return " ".join(text.split()).casefold()

    return (normalize(person.name), normalize(person.family_name))


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
    items.sort(key=_name_sort_key)
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
