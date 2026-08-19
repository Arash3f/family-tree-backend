from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pagination_request_params import PaginationRequestParams
    from ..models.role_filter_request_data import RoleFilterRequestData
    from ..models.sort_request_params_role_sort_field import SortRequestParamsRoleSortField


T = TypeVar("T", bound="FilterRoleRequest")


@_attrs_define
class FilterRoleRequest:
    """
    Attributes:
        pagination (PaginationRequestParams | Unset):
        filters (None | RoleFilterRequestData | Unset):
        sort (SortRequestParamsRoleSortField | Unset):
    """

    pagination: PaginationRequestParams | Unset = UNSET
    filters: None | RoleFilterRequestData | Unset = UNSET
    sort: SortRequestParamsRoleSortField | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.role_filter_request_data import RoleFilterRequestData

        pagination: dict[str, Any] | Unset = UNSET
        if not isinstance(self.pagination, Unset):
            pagination = self.pagination.to_dict()

        filters: dict[str, Any] | None | Unset
        if isinstance(self.filters, Unset):
            filters = UNSET
        elif isinstance(self.filters, RoleFilterRequestData):
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
        from ..models.role_filter_request_data import RoleFilterRequestData
        from ..models.sort_request_params_role_sort_field import SortRequestParamsRoleSortField

        d = dict(src_dict)
        _pagination = d.pop("pagination", UNSET)
        pagination: PaginationRequestParams | Unset
        if isinstance(_pagination, Unset):
            pagination = UNSET
        else:
            pagination = PaginationRequestParams.from_dict(_pagination)

        def _parse_filters(data: object) -> None | RoleFilterRequestData | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                filters_type_0 = RoleFilterRequestData.from_dict(data)

                return filters_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RoleFilterRequestData | Unset, data)

        filters = _parse_filters(d.pop("filters", UNSET))

        _sort = d.pop("sort", UNSET)
        sort: SortRequestParamsRoleSortField | Unset
        if isinstance(_sort, Unset):
            sort = UNSET
        else:
            sort = SortRequestParamsRoleSortField.from_dict(_sort)

        filter_role_request = cls(
            pagination=pagination,
            filters=filters,
            sort=sort,
        )

        filter_role_request.additional_properties = d
        return filter_role_request

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
