from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="RoleCreateRequest")


@_attrs_define
class RoleCreateRequest:
    """
    Attributes:
        name (None | str):
        permission_ids (list[UUID] | None):
    """

    name: None | str
    permission_ids: list[UUID] | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name: None | str
        name = self.name

        permission_ids: list[str] | None
        if isinstance(self.permission_ids, list):
            permission_ids = []
            for permission_ids_type_0_item_data in self.permission_ids:
                permission_ids_type_0_item = str(permission_ids_type_0_item_data)
                permission_ids.append(permission_ids_type_0_item)

        else:
            permission_ids = self.permission_ids

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "permission_ids": permission_ids,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        name = _parse_name(d.pop("name"))

        def _parse_permission_ids(data: object) -> list[UUID] | None:
            if data is None:
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
            return cast(list[UUID] | None, data)

        permission_ids = _parse_permission_ids(d.pop("permission_ids"))

        role_create_request = cls(
            name=name,
            permission_ids=permission_ids,
        )

        role_create_request.additional_properties = d
        return role_create_request

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
