from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.permission_sort_field import PermissionSortField
from ..models.sort_order_field import SortOrderField

T = TypeVar("T", bound="SortRequestParamsPermissionSortField")


@_attrs_define
class SortRequestParamsPermissionSortField:
    """
    Attributes:
        sort_order (SortOrderField):
        sort_by (PermissionSortField):
    """

    sort_order: SortOrderField
    sort_by: PermissionSortField
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        sort_order = self.sort_order.value

        sort_by = self.sort_by.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sort_order": sort_order,
                "sort_by": sort_by,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        sort_order = SortOrderField(d.pop("sort_order"))

        sort_by = PermissionSortField(d.pop("sort_by"))

        sort_request_params_permission_sort_field = cls(
            sort_order=sort_order,
            sort_by=sort_by,
        )

        sort_request_params_permission_sort_field.additional_properties = d
        return sort_request_params_permission_sort_field

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
