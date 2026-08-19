from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RoleUpdateDateRequest")


@_attrs_define
class RoleUpdateDateRequest:
    """
    Attributes:
        name (None | str | Unset):
        permission_ids (list[UUID] | None | Unset):
    """

    name: None | str | Unset = UNSET
    permission_ids: list[UUID] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        permission_ids: list[str] | None | Unset
        if isinstance(self.permission_ids, Unset):
            permission_ids = UNSET
        elif isinstance(self.permission_ids, list):
            permission_ids = []
            for permission_ids_type_0_item_data in self.permission_ids:
                permission_ids_type_0_item = str(permission_ids_type_0_item_data)
                permission_ids.append(permission_ids_type_0_item)

        else:
            permission_ids = self.permission_ids

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if permission_ids is not UNSET:
            field_dict["permission_ids"] = permission_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_permission_ids(data: object) -> list[UUID] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                permission_ids_type_0 = []
                _permission_ids_type_0 = data
                for permission_ids_type_0_item_data in _permission_ids_type_0:
                    permission_ids_type_0_item = UUID(permission_ids_type_0_item_data)

                    permission_ids_type_0.append(permission_ids_type_0_item)

                return permission_ids_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[UUID] | None | Unset, data)

        permission_ids = _parse_permission_ids(d.pop("permission_ids", UNSET))

        role_update_date_request = cls(
            name=name,
            permission_ids=permission_ids,
        )

        role_update_date_request.additional_properties = d
        return role_update_date_request

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
