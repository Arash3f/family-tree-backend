from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.account_type import AccountType
from ..types import UNSET, Unset

T = TypeVar("T", bound="UserUpdateDateRequest")


@_attrs_define
class UserUpdateDateRequest:
    """
    Attributes:
        username (None | str | Unset):
        fullname (None | str | Unset):
        password (None | str | Unset):
        re_password (None | str | Unset):
        role_id (None | Unset | UUID):
        account_type (AccountType | None | Unset):
    """

    username: None | str | Unset = UNSET
    fullname: None | str | Unset = UNSET
    password: None | str | Unset = UNSET
    re_password: None | str | Unset = UNSET
    role_id: None | Unset | UUID = UNSET
    account_type: AccountType | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        username: None | str | Unset
        if isinstance(self.username, Unset):
            username = UNSET
        else:
            username = self.username

        fullname: None | str | Unset
        if isinstance(self.fullname, Unset):
            fullname = UNSET
        else:
            fullname = self.fullname

        password: None | str | Unset
        if isinstance(self.password, Unset):
            password = UNSET
        else:
            password = self.password

        re_password: None | str | Unset
        if isinstance(self.re_password, Unset):
            re_password = UNSET
        else:
            re_password = self.re_password

        role_id: None | str | Unset
        if isinstance(self.role_id, Unset):
            role_id = UNSET
        elif isinstance(self.role_id, UUID):
            role_id = str(self.role_id)
        else:
            role_id = self.role_id

        account_type: None | str | Unset
        if isinstance(self.account_type, Unset):
            account_type = UNSET
        elif isinstance(self.account_type, AccountType):
            account_type = self.account_type.value
        else:
            account_type = self.account_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if username is not UNSET:
            field_dict["username"] = username
        if fullname is not UNSET:
            field_dict["fullname"] = fullname
        if password is not UNSET:
            field_dict["password"] = password
        if re_password is not UNSET:
            field_dict["re_password"] = re_password
        if role_id is not UNSET:
            field_dict["role_id"] = role_id
        if account_type is not UNSET:
            field_dict["account_type"] = account_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_username(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        username = _parse_username(d.pop("username", UNSET))

        def _parse_fullname(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        fullname = _parse_fullname(d.pop("fullname", UNSET))

        def _parse_password(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        password = _parse_password(d.pop("password", UNSET))

        def _parse_re_password(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        re_password = _parse_re_password(d.pop("re_password", UNSET))

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

        def _parse_account_type(data: object) -> AccountType | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                account_type_type_0 = AccountType(data)

                return account_type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AccountType | None | Unset, data)

        account_type = _parse_account_type(d.pop("account_type", UNSET))

        user_update_date_request = cls(
            username=username,
            fullname=fullname,
            password=password,
            re_password=re_password,
            role_id=role_id,
            account_type=account_type,
        )

        user_update_date_request.additional_properties = d
        return user_update_date_request

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
