from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.update_preferences_request_preferred_locale_type_0 import UpdatePreferencesRequestPreferredLocaleType0
from ..models.update_preferences_request_preferred_theme_type_0 import UpdatePreferencesRequestPreferredThemeType0
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdatePreferencesRequest")


@_attrs_define
class UpdatePreferencesRequest:
    """
    Attributes:
        preferred_locale (None | Unset | UpdatePreferencesRequestPreferredLocaleType0):
        preferred_theme (None | Unset | UpdatePreferencesRequestPreferredThemeType0):
    """

    preferred_locale: None | Unset | UpdatePreferencesRequestPreferredLocaleType0 = UNSET
    preferred_theme: None | Unset | UpdatePreferencesRequestPreferredThemeType0 = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        preferred_locale: None | str | Unset
        if isinstance(self.preferred_locale, Unset):
            preferred_locale = UNSET
        elif isinstance(self.preferred_locale, UpdatePreferencesRequestPreferredLocaleType0):
            preferred_locale = self.preferred_locale.value
        else:
            preferred_locale = self.preferred_locale

        preferred_theme: None | str | Unset
        if isinstance(self.preferred_theme, Unset):
            preferred_theme = UNSET
        elif isinstance(self.preferred_theme, UpdatePreferencesRequestPreferredThemeType0):
            preferred_theme = self.preferred_theme.value
        else:
            preferred_theme = self.preferred_theme

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if preferred_locale is not UNSET:
            field_dict["preferred_locale"] = preferred_locale
        if preferred_theme is not UNSET:
            field_dict["preferred_theme"] = preferred_theme

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_preferred_locale(data: object) -> None | Unset | UpdatePreferencesRequestPreferredLocaleType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                preferred_locale_type_0 = UpdatePreferencesRequestPreferredLocaleType0(data)

                return preferred_locale_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UpdatePreferencesRequestPreferredLocaleType0, data)

        preferred_locale = _parse_preferred_locale(d.pop("preferred_locale", UNSET))

        def _parse_preferred_theme(data: object) -> None | Unset | UpdatePreferencesRequestPreferredThemeType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                preferred_theme_type_0 = UpdatePreferencesRequestPreferredThemeType0(data)

                return preferred_theme_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UpdatePreferencesRequestPreferredThemeType0, data)

        preferred_theme = _parse_preferred_theme(d.pop("preferred_theme", UNSET))

        update_preferences_request = cls(
            preferred_locale=preferred_locale,
            preferred_theme=preferred_theme,
        )

        update_preferences_request.additional_properties = d
        return update_preferences_request

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
