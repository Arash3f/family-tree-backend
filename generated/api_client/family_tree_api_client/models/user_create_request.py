from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.account_type import AccountType
from ..types import UNSET, Unset

T = TypeVar("T", bound="UserCreateRequest")


@_attrs_define
class UserCreateRequest:
    """
    Attributes:
        username (str):
        fullname (str):
        password (str):
        re_password (str):
        role_id (None | Unset | UUID):
        account_type (AccountType | Unset):
    """

    username: str
    fullname: str
    password: str
    re_password: str
    role_id: None | Unset | UUID = UNSET
    account_type: AccountType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        username = self.username

        fullname = self.fullname

        password = self.password

        re_password = self.re_password

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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "username": username,
                "fullname": fullname,
                "password": password,
                "re_password": re_password,
            }
        )
        if role_id is not UNSET:
            field_dict["role_id"] = role_id
        if account_type is not UNSET:
            field_dict["account_type"] = account_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        username = d.pop("username")

        fullname = d.pop("fullname")

        password = d.pop("password")

        re_password = d.pop("re_password")

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

        user_create_request = cls(
            username=username,
            fullname=fullname,
            password=password,
            re_password=re_password,
            role_id=role_id,
            account_type=account_type,
        )

        user_create_request.additional_properties = d
        return user_create_request

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
