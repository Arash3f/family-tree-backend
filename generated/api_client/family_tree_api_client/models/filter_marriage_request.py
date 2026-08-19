from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.marriage_filter_request_data import MarriageFilterRequestData
    from ..models.pagination_request_params import PaginationRequestParams
    from ..models.sort_request_params_marriage_sort_field import SortRequestParamsMarriageSortField


T = TypeVar("T", bound="FilterMarriageRequest")


@_attrs_define
class FilterMarriageRequest:
    """
    Attributes:
        pagination (PaginationRequestParams | Unset):
        filters (MarriageFilterRequestData | None | Unset):
        sort (SortRequestParamsMarriageSortField | Unset):
    """

    pagination: PaginationRequestParams | Unset = UNSET
    filters: MarriageFilterRequestData | None | Unset = UNSET
    sort: SortRequestParamsMarriageSortField | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.marriage_filter_request_data import MarriageFilterRequestData

        pagination: dict[str, Any] | Unset = UNSET
        if not isinstance(self.pagination, Unset):
            pagination = self.pagination.to_dict()

        filters: dict[str, Any] | None | Unset
        if isinstance(self.filters, Unset):
            filters = UNSET
        elif isinstance(self.filters, MarriageFilterRequestData):
            filters = self.filters.to_dict()
        else:
            filters = self.filters

        sort: dict[str, Any] | Unset = UNSET
        if not isinstance(self.sort, Unset):
            sort = self.sort.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if pagination is not UNSET:
            field_dict["pagination"] = pagination
        if filters is not UNSET:
            field_dict["filters"] = filters
        if sort is not UNSET:
            field_dict["sort"] = sort

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.marriage_filter_request_data import MarriageFilterRequestData
        from ..models.pagination_request_params import PaginationRequestParams
        from ..models.sort_request_params_marriage_sort_field import SortRequestParamsMarriageSortField

        d = dict(src_dict)
        _pagination = d.pop("pagination", UNSET)
        pagination: PaginationRequestParams | Unset
        if isinstance(_pagination, Unset):
            pagination = UNSET
        else:
            pagination = PaginationRequestParams.from_dict(_pagination)

        def _parse_filters(data: object) -> MarriageFilterRequestData | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                filters_type_0 = MarriageFilterRequestData.from_dict(data)

                return filters_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MarriageFilterRequestData | None | Unset, data)

        filters = _parse_filters(d.pop("filters", UNSET))

        _sort = d.pop("sort", UNSET)
        sort: SortRequestParamsMarriageSortField | Unset
        if isinstance(_sort, Unset):
            sort = UNSET
        else:
            sort = SortRequestParamsMarriageSortField.from_dict(_sort)

        filter_marriage_request = cls(
            pagination=pagination,
            filters=filters,
            sort=sort,
        )

        filter_marriage_request.additional_properties = d
        return filter_marriage_request

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
