from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.ticket_category import TicketCategory
from ..models.ticket_status import TicketStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="TicketUpdateStatusResponse")


@_attrs_define
class TicketUpdateStatusResponse:
    """
    Attributes:
        id (UUID):
        title (str):
        status (TicketStatus):
        category (TicketCategory):
        created_by_user_id (UUID):
        created_by_can_manage (bool | Unset):  Default: False.
        family_tree_id (None | Unset | UUID):
        family_tree_name (None | str | Unset):
        created_at (datetime.datetime | None | Unset):
        updated_at (datetime.datetime | None | Unset):
    """

    id: UUID
    title: str
    status: TicketStatus
    category: TicketCategory
    created_by_user_id: UUID
    created_by_can_manage: bool | Unset = False
    family_tree_id: None | Unset | UUID = UNSET
    family_tree_name: None | str | Unset = UNSET
    created_at: datetime.datetime | None | Unset = UNSET
    updated_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        title = self.title

        status = self.status.value

        category = self.category.value

        created_by_user_id = str(self.created_by_user_id)

        created_by_can_manage = self.created_by_can_manage

        family_tree_id: None | str | Unset
        if isinstance(self.family_tree_id, Unset):
            family_tree_id = UNSET
        elif isinstance(self.family_tree_id, UUID):
            family_tree_id = str(self.family_tree_id)
        else:
            family_tree_id = self.family_tree_id

        family_tree_name: None | str | Unset
        if isinstance(self.family_tree_name, Unset):
            family_tree_name = UNSET
        else:
            family_tree_name = self.family_tree_name

        created_at: None | str | Unset
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        elif isinstance(self.created_at, datetime.datetime):
            created_at = self.created_at.isoformat()
        else:
            created_at = self.created_at

        updated_at: None | str | Unset
        if isinstance(self.updated_at, Unset):
            updated_at = UNSET
        elif isinstance(self.updated_at, datetime.datetime):
            updated_at = self.updated_at.isoformat()
        else:
            updated_at = self.updated_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "title": title,
                "status": status,
                "category": category,
                "created_by_user_id": created_by_user_id,
            }
        )
        if created_by_can_manage is not UNSET:
            field_dict["created_by_can_manage"] = created_by_can_manage
        if family_tree_id is not UNSET:
            field_dict["family_tree_id"] = family_tree_id
        if family_tree_name is not UNSET:
            field_dict["family_tree_name"] = family_tree_name
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        title = d.pop("title")

        status = TicketStatus(d.pop("status"))

        category = TicketCategory(d.pop("category"))

        created_by_user_id = UUID(d.pop("created_by_user_id"))

        created_by_can_manage = d.pop("created_by_can_manage", UNSET)

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

        def _parse_family_tree_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        family_tree_name = _parse_family_tree_name(d.pop("family_tree_name", UNSET))

        def _parse_created_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_at_type_0 = datetime.datetime.fromisoformat(data)

                return created_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        def _parse_updated_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                updated_at_type_0 = datetime.datetime.fromisoformat(data)

                return updated_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        updated_at = _parse_updated_at(d.pop("updated_at", UNSET))

        ticket_update_status_response = cls(
            id=id,
            title=title,
            status=status,
            category=category,
            created_by_user_id=created_by_user_id,
            created_by_can_manage=created_by_can_manage,
            family_tree_id=family_tree_id,
            family_tree_name=family_tree_name,
            created_at=created_at,
            updated_at=updated_at,
        )

        ticket_update_status_response.additional_properties = d
        return ticket_update_status_response

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
