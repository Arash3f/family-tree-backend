from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="FamilyTreeResponse")


@_attrs_define
class FamilyTreeResponse:
    """
    Attributes:
        id (UUID):
        name (str):
        owner_user_id (UUID):
        my_permissions (list[str] | Unset):
    """

    id: UUID
    name: str
    owner_user_id: UUID
    my_permissions: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        owner_user_id = str(self.owner_user_id)

        my_permissions: list[str] | Unset = UNSET
        if not isinstance(self.my_permissions, Unset):
            my_permissions = self.my_permissions

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "owner_user_id": owner_user_id,
            }
        )
        if my_permissions is not UNSET:
            field_dict["my_permissions"] = my_permissions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        owner_user_id = UUID(d.pop("owner_user_id"))

        my_permissions = cast(list[str], d.pop("my_permissions", UNSET))

        family_tree_response = cls(
            id=id,
            name=name,
            owner_user_id=owner_user_id,
            my_permissions=my_permissions,
        )

        family_tree_response.additional_properties = d
        return family_tree_response

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
