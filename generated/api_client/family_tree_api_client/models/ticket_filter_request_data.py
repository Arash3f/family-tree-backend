from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.ticket_category import TicketCategory
from ..models.ticket_status import TicketStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="TicketFilterRequestData")


@_attrs_define
class TicketFilterRequestData:
    """
    Attributes:
        id (None | Unset | UUID):
        title (None | str | Unset):
        status (None | TicketStatus | Unset):
        category (None | TicketCategory | Unset):
        family_tree_id (None | Unset | UUID):
        created_by_user_id (None | Unset | UUID):
    """

    id: None | Unset | UUID = UNSET
    title: None | str | Unset = UNSET
    status: None | TicketStatus | Unset = UNSET
    category: None | TicketCategory | Unset = UNSET
    family_tree_id: None | Unset | UUID = UNSET
    created_by_user_id: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        elif isinstance(self.id, UUID):
            id = str(self.id)
        else:
            id = self.id

        title: None | str | Unset
        if isinstance(self.title, Unset):
            title = UNSET
        else:
            title = self.title

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, TicketStatus):
            status = self.status.value
        else:
            status = self.status

        category: None | str | Unset
        if isinstance(self.category, Unset):
            category = UNSET
        elif isinstance(self.category, TicketCategory):
            category = self.category.value
        else:
            category = self.category

        family_tree_id: None | str | Unset
        if isinstance(self.family_tree_id, Unset):
            family_tree_id = UNSET
        elif isinstance(self.family_tree_id, UUID):
            family_tree_id = str(self.family_tree_id)
        else:
            family_tree_id = self.family_tree_id

        created_by_user_id: None | str | Unset
        if isinstance(self.created_by_user_id, Unset):
            created_by_user_id = UNSET
        elif isinstance(self.created_by_user_id, UUID):
            created_by_user_id = str(self.created_by_user_id)
        else:
            created_by_user_id = self.created_by_user_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if title is not UNSET:
            field_dict["title"] = title
        if status is not UNSET:
            field_dict["status"] = status
        if category is not UNSET:
            field_dict["category"] = category
        if family_tree_id is not UNSET:
            field_dict["family_tree_id"] = family_tree_id
        if created_by_user_id is not UNSET:
            field_dict["created_by_user_id"] = created_by_user_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                id_type_0 = UUID(data)

                return id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_title(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        title = _parse_title(d.pop("title", UNSET))

        def _parse_status(data: object) -> None | TicketStatus | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                status_type_0 = TicketStatus(data)

                return status_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TicketStatus | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_category(data: object) -> None | TicketCategory | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                category_type_0 = TicketCategory(data)

                return category_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TicketCategory | Unset, data)

        category = _parse_category(d.pop("category", UNSET))

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

        def _parse_created_by_user_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_by_user_id_type_0 = UUID(data)

                return created_by_user_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        created_by_user_id = _parse_created_by_user_id(d.pop("created_by_user_id", UNSET))

        ticket_filter_request_data = cls(
            id=id,
            title=title,
            status=status,
            category=category,
            family_tree_id=family_tree_id,
            created_by_user_id=created_by_user_id,
        )

        ticket_filter_request_data.additional_properties = d
        return ticket_filter_request_data

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
