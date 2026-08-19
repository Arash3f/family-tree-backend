from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DivorceRequest")


@_attrs_define
class DivorceRequest:
    """
    Attributes:
        marriage_id (UUID):
        divorced_at (datetime.date):
    """

    marriage_id: UUID
    divorced_at: datetime.date
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        marriage_id = str(self.marriage_id)

        divorced_at = self.divorced_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "marriage_id": marriage_id,
                "divorced_at": divorced_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        marriage_id = UUID(d.pop("marriage_id"))

        divorced_at = datetime.date.fromisoformat(d.pop("divorced_at"))

        divorce_request = cls(
            marriage_id=marriage_id,
            divorced_at=divorced_at,
        )

        divorce_request.additional_properties = d
        return divorce_request

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
