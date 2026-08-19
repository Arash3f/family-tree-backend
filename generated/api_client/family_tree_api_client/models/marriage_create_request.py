from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="MarriageCreateRequest")


@_attrs_define
class MarriageCreateRequest:
    """
    Attributes:
        spouse_a_id (UUID):
        spouse_b_id (UUID):
        married_at (datetime.date):
    """

    spouse_a_id: UUID
    spouse_b_id: UUID
    married_at: datetime.date
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        spouse_a_id = str(self.spouse_a_id)

        spouse_b_id = str(self.spouse_b_id)

        married_at = self.married_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "spouse_a_id": spouse_a_id,
                "spouse_b_id": spouse_b_id,
                "married_at": married_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        spouse_a_id = UUID(d.pop("spouse_a_id"))

        spouse_b_id = UUID(d.pop("spouse_b_id"))

        married_at = datetime.date.fromisoformat(d.pop("married_at"))

        marriage_create_request = cls(
            spouse_a_id=spouse_a_id,
            spouse_b_id=spouse_b_id,
            married_at=married_at,
        )

        marriage_create_request.additional_properties = d
        return marriage_create_request

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
