from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

# Upper bound on how many rows one request may pull back. Without it a single
# caller can ask for the whole table and turn any list endpoint into a cheap
# denial of service.
MAX_PAGE_SIZE = 100

# Hard cap when ``get_all`` skips normal paging. Still bounds a single response
# so an unfiltered users/tickets list cannot dump the whole database.
MAX_GET_ALL_SIZE = 10_000


class PaginatedResult(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class PaginationParams(BaseModel):
    page: int
    page_size: int
    offset: int
    # When true, return every matching row (up to ``MAX_GET_ALL_SIZE``).
    get_all: bool = False
