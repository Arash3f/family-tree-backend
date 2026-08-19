from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.tree_member_role import TreeMemberRole
from ..types import UNSET, Unset

T = TypeVar("T", bound="TreeMembershipResponse")


@_attrs_define
class TreeMembershipResponse:
    """
    Attributes:
        id (UUID):
        tree_id (UUID):
        user_id (UUID):
        role (TreeMemberRole):
        permissions (list[str] | Unset):
        username (None | str | Unset):
    """

    id: UUID
    tree_id: UUID
    user_id: UUID
    role: TreeMemberRole
    permissions: list[str] | Unset = UNSET
    username: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        tree_id = str(self.tree_id)

        user_id = str(self.user_id)

        role = self.role.value

        permissions: list[str] | Unset = UNSET
        if not isinstance(self.permissions, Unset):
            permissions = self.permissions

        username: None | str | Unset
        if isinstance(self.username, Unset):
            username = UNSET
        else:
            username = self.username

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "tree_id": tree_id,
                "user_id": user_id,
                "role": role,
            }
        )
        if permissions is not UNSET:
            field_dict["permissions"] = permissions
        if username is not UNSET:
            field_dict["username"] = username

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        tree_id = UUID(d.pop("tree_id"))

        user_id = UUID(d.pop("user_id"))

        role = TreeMemberRole(d.pop("role"))

        permissions = cast(list[str], d.pop("permissions", UNSET))

        def _parse_username(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        username = _parse_username(d.pop("username", UNSET))

        tree_membership_response = cls(
            id=id,
            tree_id=tree_id,
            user_id=user_id,
            role=role,
            permissions=permissions,
            username=username,
        )

        tree_membership_response.additional_properties = d
        return tree_membership_response

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
