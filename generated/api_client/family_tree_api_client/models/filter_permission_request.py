from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pagination_request_params import PaginationRequestParams
    from ..models.permission_filter_request_data import PermissionFilterRequestData
    from ..models.sort_request_params_permission_sort_field import SortRequestParamsPermissionSortField


T = TypeVar("T", bound="FilterPermissionRequest")


@_attrs_define
class FilterPermissionRequest:
    """
    Attributes:
        pagination (PaginationRequestParams | Unset):
        filters (None | PermissionFilterRequestData | Unset):
        sort (SortRequestParamsPermissionSortField | Unset):
    """

    pagination: PaginationRequestParams | Unset = UNSET
    filters: None | PermissionFilterRequestData | Unset = UNSET
    sort: SortRequestParamsPermissionSortField | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.permission_filter_request_data import PermissionFilterRequestData

        pagination: dict[str, Any] | Unset = UNSET
        if not isinstance(self.pagination, Unset):
            pagination = self.pagination.to_dict()

        filters: dict[str, Any] | None | Unset
        if isinstance(self.filters, Unset):
            filters = UNSET
        elif isinstance(self.filters, PermissionFilterRequestData):
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
        from ..models.pagination_request_params import PaginationRequestParams
        from ..models.permission_filter_request_data import PermissionFilterRequestData
        from ..models.sort_request_params_permission_sort_field import SortRequestParamsPermissionSortField

        d = dict(src_dict)
        _pagination = d.pop("pagination", UNSET)
        pagination: PaginationRequestParams | Unset
        if isinstance(_pagination, Unset):
            pagination = UNSET
        else:
            pagination = PaginationRequestParams.from_dict(_pagination)

        def _parse_filters(data: object) -> None | PermissionFilterRequestData | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                filters_type_0 = PermissionFilterRequestData.from_dict(data)

                return filters_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PermissionFilterRequestData | Unset, data)

        filters = _parse_filters(d.pop("filters", UNSET))

        _sort = d.pop("sort", UNSET)
        sort: SortRequestParamsPermissionSortField | Unset
        if isinstance(_sort, Unset):
            sort = UNSET
        else:
            sort = SortRequestParamsPermissionSortField.from_dict(_sort)

        filter_permission_request = cls(
            pagination=pagination,
            filters=filters,
            sort=sort,
        )

        filter_permission_request.additional_properties = d
        return filter_permission_request

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
