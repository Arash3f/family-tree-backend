from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="TreeUsageResponse")


@_attrs_define
class TreeUsageResponse:
    """
    Attributes:
        tree_id (UUID):
        name (str):
        persons (int):
        marriages (int):
    """

    tree_id: UUID
    name: str
    persons: int
    marriages: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        tree_id = str(self.tree_id)

        name = self.name

        persons = self.persons

        marriages = self.marriages

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tree_id": tree_id,
                "name": name,
                "persons": persons,
                "marriages": marriages,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        tree_id = UUID(d.pop("tree_id"))

        name = d.pop("name")

        persons = d.pop("persons")

        marriages = d.pop("marriages")

        tree_usage_response = cls(
            tree_id=tree_id,
            name=name,
            persons=persons,
            marriages=marriages,
        )

        tree_usage_response.additional_properties = d
        return tree_usage_response

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
