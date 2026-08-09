import pytest

from app.domain.shared.dto.pagination_dto import MAX_PAGE_SIZE
from app.presentation.rest.schemas.dto.common import PaginationRequestParams
from app.utils.app_exception import AppException
from app.utils.error_codes import ErrorCode


def test_defaults_are_within_bounds():
    params = PaginationRequestParams()
    assert params.page == 1
    assert 1 <= params.page_size <= MAX_PAGE_SIZE
    assert params.offset == 0


def test_page_size_at_the_cap_is_allowed():
    assert PaginationRequestParams(page_size=MAX_PAGE_SIZE).page_size == MAX_PAGE_SIZE


def test_page_size_above_the_cap_is_rejected():
    """Without a cap one caller could ask a list endpoint for the whole table."""
    with pytest.raises(AppException) as exc_info:
        PaginationRequestParams(page_size=MAX_PAGE_SIZE + 1)

    assert exc_info.value.code == ErrorCode.INVALID_PAGE_SIZE
    assert exc_info.value.status_code == 422


@pytest.mark.parametrize("page_size", [0, -1])
def test_non_positive_page_size_is_rejected(page_size: int):
    with pytest.raises(AppException) as exc_info:
        PaginationRequestParams(page_size=page_size)

    assert exc_info.value.code == ErrorCode.INVALID_PAGE_SIZE


def test_non_positive_page_is_rejected():
    with pytest.raises(AppException) as exc_info:
        PaginationRequestParams(page=0)

    assert exc_info.value.code == ErrorCode.INVALID_PAGE


def test_negative_offset_is_rejected():
    with pytest.raises(AppException) as exc_info:
        PaginationRequestParams(offset=-1)

    assert exc_info.value.code == ErrorCode.INVALID_PAGE
