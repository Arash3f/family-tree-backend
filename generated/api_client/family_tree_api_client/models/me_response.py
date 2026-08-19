from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

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
        session_id (UUID):
        fullname (str | Unset):  Default: ''.
        role_id (None | Unset | UUID):
        role_name (None | str | Unset):
        permissions (list[str] | Unset):
        permission_details (list[MePermissionItem] | Unset):
        account_type (str | Unset):  Default: 'free'.
    """

    id: UUID
    username: str
    session_id: UUID
    fullname: str | Unset = ""
    role_id: None | Unset | UUID = UNSET
    role_name: None | str | Unset = UNSET
    permissions: list[str] | Unset = UNSET
    permission_details: list[MePermissionItem] | Unset = UNSET
    account_type: str | Unset = "free"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        username = self.username

        session_id = str(self.session_id)

        fullname = self.fullname

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

        account_type = self.account_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "username": username,
                "session_id": session_id,
            }
        )
        if fullname is not UNSET:
            field_dict["fullname"] = fullname
        if role_id is not UNSET:
            field_dict["role_id"] = role_id
        if role_name is not UNSET:
            field_dict["role_name"] = role_name
        if permissions is not UNSET:
            field_dict["permissions"] = permissions
        if permission_details is not UNSET:
            field_dict["permission_details"] = permission_details
        if account_type is not UNSET:
            field_dict["account_type"] = account_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.me_permission_item import MePermissionItem

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        username = d.pop("username")

        session_id = UUID(d.pop("session_id"))

        fullname = d.pop("fullname", UNSET)

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

        account_type = d.pop("account_type", UNSET)

        me_response = cls(
            id=id,
            username=username,
            session_id=session_id,
            fullname=fullname,
            role_id=role_id,
            role_name=role_name,
            permissions=permissions,
            permission_details=permission_details,
            account_type=account_type,
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
