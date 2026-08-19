from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.parent_relationship_type import ParentRelationshipType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ParentLinkRequest")


@_attrs_define
class ParentLinkRequest:
    """
    Attributes:
        parent_id (UUID):
        relationship_type (ParentRelationshipType | Unset):
    """

    parent_id: UUID
    relationship_type: ParentRelationshipType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        parent_id = str(self.parent_id)

        relationship_type: str | Unset = UNSET
        if not isinstance(self.relationship_type, Unset):
            relationship_type = self.relationship_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "parent_id": parent_id,
            }
        )
        if relationship_type is not UNSET:
            field_dict["relationship_type"] = relationship_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        parent_id = UUID(d.pop("parent_id"))

        _relationship_type = d.pop("relationship_type", UNSET)
        relationship_type: ParentRelationshipType | Unset
        if isinstance(_relationship_type, Unset):
            relationship_type = UNSET
        else:
            relationship_type = ParentRelationshipType(_relationship_type)

        parent_link_request = cls(
            parent_id=parent_id,
            relationship_type=relationship_type,
        )

        parent_link_request.additional_properties = d
        return parent_link_request

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
