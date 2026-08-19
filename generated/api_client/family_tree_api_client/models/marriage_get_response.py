from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="MarriageGetResponse")


@_attrs_define
class MarriageGetResponse:
    """
    Attributes:
        id (UUID):
        spouse_a_id (UUID):
        spouse_b_id (UUID):
        married_at (datetime.date | None):
        divorced_at (datetime.date | None):
    """

    id: UUID
    spouse_a_id: UUID
    spouse_b_id: UUID
    married_at: datetime.date | None
    divorced_at: datetime.date | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        spouse_a_id = str(self.spouse_a_id)

        spouse_b_id = str(self.spouse_b_id)

        married_at: None | str
        if isinstance(self.married_at, datetime.date):
            married_at = self.married_at.isoformat()
        else:
            married_at = self.married_at

        divorced_at: None | str
        if isinstance(self.divorced_at, datetime.date):
            divorced_at = self.divorced_at.isoformat()
        else:
            divorced_at = self.divorced_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "spouse_a_id": spouse_a_id,
                "spouse_b_id": spouse_b_id,
                "married_at": married_at,
                "divorced_at": divorced_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        spouse_a_id = UUID(d.pop("spouse_a_id"))

        spouse_b_id = UUID(d.pop("spouse_b_id"))

        def _parse_married_at(data: object) -> datetime.date | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                married_at_type_0 = datetime.date.fromisoformat(data)

                return married_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.date | None, data)

        married_at = _parse_married_at(d.pop("married_at"))

        def _parse_divorced_at(data: object) -> datetime.date | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                divorced_at_type_0 = datetime.date.fromisoformat(data)

                return divorced_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.date | None, data)

        divorced_at = _parse_divorced_at(d.pop("divorced_at"))

        marriage_get_response = cls(
            id=id,
            spouse_a_id=spouse_a_id,
            spouse_b_id=spouse_b_id,
            married_at=married_at,
            divorced_at=divorced_at,
        )

        marriage_get_response.additional_properties = d
        return marriage_get_response

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
