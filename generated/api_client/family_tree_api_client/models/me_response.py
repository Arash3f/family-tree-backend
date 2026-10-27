from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.me_response_preferred_locale_type_0 import MeResponsePreferredLocaleType0
from ..models.me_response_preferred_theme_type_0 import MeResponsePreferredThemeType0
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.me_permission_item import MePermissionItem


T = TypeVar("T", bound="MeResponse")


@_attrs_define
class MeResponse:
    """
    Attributes:
        id (UUID):
        username (str):
        fullname (str | Unset):  Default: ''.
        email (None | str | Unset):
        phone (None | str | Unset):
        role_id (None | Unset | UUID):
        role_name (None | str | Unset):
        permissions (list[str] | Unset):
        permission_details (list[MePermissionItem] | Unset):
        session_id (None | Unset | UUID):
        is_impersonating (bool | Unset):  Default: False.
        account_type (str | Unset):  Default: 'free'.
        paid_until (datetime.date | None | Unset):
        preferred_locale (MeResponsePreferredLocaleType0 | None | Unset):
        preferred_theme (MeResponsePreferredThemeType0 | None | Unset):
    """

    id: UUID
    username: str
    fullname: str | Unset = ""
    email: None | str | Unset = UNSET
    phone: None | str | Unset = UNSET
    role_id: None | Unset | UUID = UNSET
    role_name: None | str | Unset = UNSET
    permissions: list[str] | Unset = UNSET
    permission_details: list[MePermissionItem] | Unset = UNSET
    session_id: None | Unset | UUID = UNSET
    is_impersonating: bool | Unset = False
    account_type: str | Unset = "free"
    paid_until: datetime.date | None | Unset = UNSET
    preferred_locale: MeResponsePreferredLocaleType0 | None | Unset = UNSET
    preferred_theme: MeResponsePreferredThemeType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        username = self.username

        fullname = self.fullname

        email: None | str | Unset
        if isinstance(self.email, Unset):
            email = UNSET
        else:
            email = self.email

        phone: None | str | Unset
        if isinstance(self.phone, Unset):
            phone = UNSET
        else:
            phone = self.phone

        role_id: None | str | Unset
        if isinstance(self.role_id, Unset):
            role_id = UNSET
        elif isinstance(self.role_id, UUID):
            role_id = str(self.role_id)
        else:
            role_id = self.role_id

        role_name: None | str | Unset
        if isinstance(self.role_name, Unset):
            role_name = UNSET
        else:
            role_name = self.role_name

        permissions: list[str] | Unset = UNSET
        if not isinstance(self.permissions, Unset):
            permissions = self.permissions

        permission_details: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.permission_details, Unset):
            permission_details = []
            for permission_details_item_data in self.permission_details:
                permission_details_item = permission_details_item_data.to_dict()
                permission_details.append(permission_details_item)

        session_id: None | str | Unset
        if isinstance(self.session_id, Unset):
            session_id = UNSET
        elif isinstance(self.session_id, UUID):
            session_id = str(self.session_id)
        else:
            session_id = self.session_id

        is_impersonating = self.is_impersonating

        account_type = self.account_type

        paid_until: None | str | Unset
        if isinstance(self.paid_until, Unset):
            paid_until = UNSET
        elif isinstance(self.paid_until, datetime.date):
            paid_until = self.paid_until.isoformat()
        else:
            paid_until = self.paid_until

        preferred_locale: None | str | Unset
        if isinstance(self.preferred_locale, Unset):
            preferred_locale = UNSET
        elif isinstance(self.preferred_locale, MeResponsePreferredLocaleType0):
            preferred_locale = self.preferred_locale.value
        else:
            preferred_locale = self.preferred_locale

        preferred_theme: None | str | Unset
        if isinstance(self.preferred_theme, Unset):
            preferred_theme = UNSET
        elif isinstance(self.preferred_theme, MeResponsePreferredThemeType0):
            preferred_theme = self.preferred_theme.value
        else:
            preferred_theme = self.preferred_theme

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "username": username,
            }
        )
        if fullname is not UNSET:
            field_dict["fullname"] = fullname
        if email is not UNSET:
            field_dict["email"] = email
        if phone is not UNSET:
            field_dict["phone"] = phone
        if role_id is not UNSET:
            field_dict["role_id"] = role_id
        if role_name is not UNSET:
            field_dict["role_name"] = role_name
        if permissions is not UNSET:
            field_dict["permissions"] = permissions
        if permission_details is not UNSET:
            field_dict["permission_details"] = permission_details
        if session_id is not UNSET:
            field_dict["session_id"] = session_id
        if is_impersonating is not UNSET:
            field_dict["is_impersonating"] = is_impersonating
        if account_type is not UNSET:
            field_dict["account_type"] = account_type
        if paid_until is not UNSET:
            field_dict["paid_until"] = paid_until
        if preferred_locale is not UNSET:
            field_dict["preferred_locale"] = preferred_locale
        if preferred_theme is not UNSET:
            field_dict["preferred_theme"] = preferred_theme

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.me_permission_item import MePermissionItem  # noqa: PLC0415

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        username = d.pop("username")

        fullname = d.pop("fullname", UNSET)

        def _parse_email(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        email = _parse_email(d.pop("email", UNSET))

        def _parse_phone(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        phone = _parse_phone(d.pop("phone", UNSET))

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

        def _parse_role_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        role_name = _parse_role_name(d.pop("role_name", UNSET))

        permissions = cast(list[str], d.pop("permissions", UNSET))

        _permission_details = d.pop("permission_details", UNSET)
        permission_details: list[MePermissionItem] | Unset = UNSET
        if _permission_details is not UNSET:
            permission_details = []
            for permission_details_item_data in _permission_details:
                permission_details_item = MePermissionItem.from_dict(permission_details_item_data)

                permission_details.append(permission_details_item)

        def _parse_session_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                session_id_type_0 = UUID(data)

                return session_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        session_id = _parse_session_id(d.pop("session_id", UNSET))

        is_impersonating = d.pop("is_impersonating", UNSET)

        account_type = d.pop("account_type", UNSET)

        def _parse_paid_until(data: object) -> datetime.date | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                paid_until_type_0 = datetime.date.fromisoformat(data)

                return paid_until_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.date | None | Unset, data)

        paid_until = _parse_paid_until(d.pop("paid_until", UNSET))

        def _parse_preferred_locale(data: object) -> MeResponsePreferredLocaleType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                preferred_locale_type_0 = MeResponsePreferredLocaleType0(data)

                return preferred_locale_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MeResponsePreferredLocaleType0 | None | Unset, data)

        preferred_locale = _parse_preferred_locale(d.pop("preferred_locale", UNSET))

        def _parse_preferred_theme(data: object) -> MeResponsePreferredThemeType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                preferred_theme_type_0 = MeResponsePreferredThemeType0(data)

                return preferred_theme_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MeResponsePreferredThemeType0 | None | Unset, data)

        preferred_theme = _parse_preferred_theme(d.pop("preferred_theme", UNSET))

        me_response = cls(
            id=id,
            username=username,
            fullname=fullname,
            email=email,
            phone=phone,
            role_id=role_id,
            role_name=role_name,
            permissions=permissions,
            permission_details=permission_details,
            session_id=session_id,
            is_impersonating=is_impersonating,
            account_type=account_type,
            paid_until=paid_until,
            preferred_locale=preferred_locale,
            preferred_theme=preferred_theme,
        )

        me_response.additional_properties = d
        return me_response

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
