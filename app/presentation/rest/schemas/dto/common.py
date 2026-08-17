from dataclasses import dataclass
from datetime import date
from typing import Annotated, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, field_validator, model_validator

from app.domain.shared.dto.pagination_dto import MAX_PAGE_SIZE
from app.domain.shared.dto.sorter_dto import SortOrderField
from app.presentation.utils.date_convert import parse_user_date
from app.utils.app_exception import AppException
from app.utils.error_codes import ErrorCode


@dataclass
class IdRequest:
    id: UUID


@dataclass
class ResultResponse:
    result: str


T = TypeVar("T")


def _coerce_iso_date(value):
    return parse_user_date(value)


IsoDate = Annotated[date, BeforeValidator(_coerce_iso_date)]


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class PaginationRequestParams(BaseModel):
    page: int = 1
    page_size: int = 30
    offset: int = 0

    @model_validator(mode="after")
    def check_bounds(self) -> "PaginationRequestParams":
        """Reject out-of-range paging before it reaches the database.

        Raises the application's own exceptions rather than letting Pydantic
        produce a ValidationError, so REST and GraphQL callers both get the
        usual error_code payload.
        """
        if self.page < 1:
            raise AppException(
                code=ErrorCode.INVALID_PAGE,
                status_code=422,
                detail=["Page must be greater than or equal to 1."],
            )

        if self.page_size < 1:
            raise AppException(
                code=ErrorCode.INVALID_PAGE_SIZE,
                status_code=422,
                detail=["Page size must be greater than or equal to 1."],
            )

        if self.page_size > MAX_PAGE_SIZE:
            raise AppException(
                code=ErrorCode.INVALID_PAGE_SIZE,
                status_code=422,
                detail=[f"Page size must not exceed {MAX_PAGE_SIZE}."],
            )

        if self.offset < 0:
            raise AppException(
                code=ErrorCode.INVALID_PAGE,
                status_code=422,
                detail=["Offset must be greater than or equal to 0."],
            )

        return self


class SortRequestParams(BaseModel, Generic[T]):
    sort_order: SortOrderField
    sort_by: T


@dataclass
class RangeRequest(Generic[T]):
    min: T | None = None
    max: T | None = None

    @field_validator("min", mode="before")
    def parse_iso_min(cls, v):
        return _coerce_iso_date(v)

    @field_validator("max", mode="before")
    def parse_iso_max(cls, v):
        return _coerce_iso_date(v)
