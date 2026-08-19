from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.account_type import AccountType
from ..types import UNSET, Unset

T = TypeVar("T", bound="UserModel")


@_attrs_define
class UserModel:
    """
    Attributes:
        id (UUID):
        username (str):
        fullname (str):
        role_id (None | Unset | UUID):
        account_type (AccountType | Unset):
        last_session_at (datetime.datetime | None | Unset):
    """

    id: UUID
    username: str
    fullname: str
    role_id: None | Unset | UUID = UNSET
    account_type: AccountType | Unset = UNSET
    last_session_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        username = self.username

        fullname = self.fullname

        role_id: None | str | Unset
        if isinstance(self.role_id, Unset):
            role_id = UNSET
        elif isinstance(self.role_id, UUID):
            role_id = str(self.role_id)
        else:
            role_id = self.role_id

        account_type: str | Unset = UNSET
        if not isinstance(self.account_type, Unset):
            account_type = self.account_type.value

        last_session_at: None | str | Unset
        if isinstance(self.last_session_at, Unset):
            last_session_at = UNSET
        elif isinstance(self.last_session_at, datetime.datetime):
            last_session_at = self.last_session_at.isoformat()
        else:
            last_session_at = self.last_session_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "username": username,
                "fullname": fullname,
            }
        )
        if role_id is not UNSET:
            field_dict["role_id"] = role_id
        if account_type is not UNSET:
            field_dict["account_type"] = account_type
        if last_session_at is not UNSET:
            field_dict["last_session_at"] = last_session_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        username = d.pop("username")

        fullname = d.pop("fullname")

        def _parse_role_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                role_id_type_0 = UUID(data)

                return role_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        role_id = _parse_role_id(d.pop("role_id", UNSET))

        _account_type = d.pop("account_type", UNSET)
        account_type: AccountType | Unset
        if isinstance(_account_type, Unset):
            account_type = UNSET
        else:
            account_type = AccountType(_account_type)

        def _parse_last_session_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_session_at_type_0 = datetime.datetime.fromisoformat(data)

                return last_session_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        last_session_at = _parse_last_session_at(d.pop("last_session_at", UNSET))

        user_model = cls(
            id=id,
            username=username,
            fullname=fullname,
            role_id=role_id,
            account_type=account_type,
            last_session_at=last_session_at,
        )

        user_model.additional_properties = d
        return user_model

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
