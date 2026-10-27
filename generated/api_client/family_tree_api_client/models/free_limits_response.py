from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="FreeLimitsResponse")


@_attrs_define
class FreeLimitsResponse:
    """
    Attributes:
        owned_trees (int):
        persons_per_tree (int):
        marriages_per_tree (int):
    """

    owned_trees: int
    persons_per_tree: int
    marriages_per_tree: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        owned_trees = self.owned_trees

        persons_per_tree = self.persons_per_tree

        marriages_per_tree = self.marriages_per_tree

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "owned_trees": owned_trees,
                "persons_per_tree": persons_per_tree,
                "marriages_per_tree": marriages_per_tree,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        owned_trees = d.pop("owned_trees")

        persons_per_tree = d.pop("persons_per_tree")

        marriages_per_tree = d.pop("marriages_per_tree")

        free_limits_response = cls(
            owned_trees=owned_trees,
            persons_per_tree=persons_per_tree,
            marriages_per_tree=marriages_per_tree,
        )

        free_limits_response.additional_properties = d
        return free_limits_response

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
