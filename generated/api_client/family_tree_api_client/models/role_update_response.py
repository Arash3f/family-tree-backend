from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RoleUpdateResponse")


@_attrs_define
class RoleUpdateResponse:
    """
    Attributes:
        id (UUID):
        name (str):
        permission_ids (list[UUID] | Unset):
    """

    id: UUID
    name: str
    permission_ids: list[UUID] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        permission_ids: list[str] | Unset = UNSET
        if not isinstance(self.permission_ids, Unset):
            permission_ids = []
            for permission_ids_item_data in self.permission_ids:
                permission_ids_item = str(permission_ids_item_data)
                permission_ids.append(permission_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
            }
        )
        if permission_ids is not UNSET:
            field_dict["permission_ids"] = permission_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        _permission_ids = d.pop("permission_ids", UNSET)
        permission_ids: list[UUID] | Unset = UNSET
        if _permission_ids is not UNSET:
            permission_ids = []
            for permission_ids_item_data in _permission_ids:
                permission_ids_item = UUID(permission_ids_item_data)

                permission_ids.append(permission_ids_item)

        role_update_response = cls(
            id=id,
            name=name,
            permission_ids=permission_ids,
        )

        role_update_response.additional_properties = d
        return role_update_response

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
