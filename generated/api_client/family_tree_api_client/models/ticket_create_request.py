from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.ticket_category import TicketCategory
from ..types import UNSET, Unset

T = TypeVar("T", bound="TicketCreateRequest")


@_attrs_define
class TicketCreateRequest:
    """
    Attributes:
        title (str):
        body (str):
        category (TicketCategory):
        family_tree_id (None | Unset | UUID):
    """

    title: str
    body: str
    category: TicketCategory
    family_tree_id: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        title = self.title

        body = self.body

        category = self.category.value

        family_tree_id: None | str | Unset
        if isinstance(self.family_tree_id, Unset):
            family_tree_id = UNSET
        elif isinstance(self.family_tree_id, UUID):
            family_tree_id = str(self.family_tree_id)
        else:
            family_tree_id = self.family_tree_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "title": title,
                "body": body,
                "category": category,
            }
        )
        if family_tree_id is not UNSET:
            field_dict["family_tree_id"] = family_tree_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        title = d.pop("title")

        body = d.pop("body")

        category = TicketCategory(d.pop("category"))

        def _parse_family_tree_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                family_tree_id_type_0 = UUID(data)

                return family_tree_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        family_tree_id = _parse_family_tree_id(d.pop("family_tree_id", UNSET))

        ticket_create_request = cls(
            title=title,
            body=body,
            category=category,
            family_tree_id=family_tree_id,
        )

        ticket_create_request.additional_properties = d
        return ticket_create_request

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
