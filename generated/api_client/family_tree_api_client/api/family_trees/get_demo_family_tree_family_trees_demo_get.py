from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.family_tree_response import FamilyTreeResponse
from ...models.get_demo_family_tree_family_trees_demo_get_locale import GetDemoFamilyTreeFamilyTreesDemoGetLocale
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    locale: GetDemoFamilyTreeFamilyTreesDemoGetLocale | Unset = GetDemoFamilyTreeFamilyTreesDemoGetLocale.EN,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_locale: str | Unset = UNSET
    if not isinstance(locale, Unset):
        json_locale = locale.value

    params["locale"] = json_locale

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/family-trees/demo",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> FamilyTreeResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = FamilyTreeResponse.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[FamilyTreeResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    locale: GetDemoFamilyTreeFamilyTreesDemoGetLocale | Unset = GetDemoFamilyTreeFamilyTreesDemoGetLocale.EN,
) -> Response[FamilyTreeResponse | HTTPValidationError]:
    """The publicly readable demo tree for a UI locale

     Point a signed-out visitor at the demo tree for their language.

    Declared above `/{tree_id}` so the literal path wins the match, and the only
    route here that takes no credentials. `my_permissions` comes back as the
    read-only demo set, which is the same field the client already reads to
    decide what to render — so the demo needs no second rendering path.

    Args:
        locale (GetDemoFamilyTreeFamilyTreesDemoGetLocale | Unset): UI locale: `fa` and `en` may
            point at different demo trees. Default: GetDemoFamilyTreeFamilyTreesDemoGetLocale.EN.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FamilyTreeResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        locale=locale,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    locale: GetDemoFamilyTreeFamilyTreesDemoGetLocale | Unset = GetDemoFamilyTreeFamilyTreesDemoGetLocale.EN,
) -> FamilyTreeResponse | HTTPValidationError | None:
    """The publicly readable demo tree for a UI locale

     Point a signed-out visitor at the demo tree for their language.

    Declared above `/{tree_id}` so the literal path wins the match, and the only
    route here that takes no credentials. `my_permissions` comes back as the
    read-only demo set, which is the same field the client already reads to
    decide what to render — so the demo needs no second rendering path.

    Args:
        locale (GetDemoFamilyTreeFamilyTreesDemoGetLocale | Unset): UI locale: `fa` and `en` may
            point at different demo trees. Default: GetDemoFamilyTreeFamilyTreesDemoGetLocale.EN.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FamilyTreeResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        locale=locale,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    locale: GetDemoFamilyTreeFamilyTreesDemoGetLocale | Unset = GetDemoFamilyTreeFamilyTreesDemoGetLocale.EN,
) -> Response[FamilyTreeResponse | HTTPValidationError]:
    """The publicly readable demo tree for a UI locale

     Point a signed-out visitor at the demo tree for their language.

    Declared above `/{tree_id}` so the literal path wins the match, and the only
    route here that takes no credentials. `my_permissions` comes back as the
    read-only demo set, which is the same field the client already reads to
    decide what to render — so the demo needs no second rendering path.

    Args:
        locale (GetDemoFamilyTreeFamilyTreesDemoGetLocale | Unset): UI locale: `fa` and `en` may
            point at different demo trees. Default: GetDemoFamilyTreeFamilyTreesDemoGetLocale.EN.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FamilyTreeResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        locale=locale,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    locale: GetDemoFamilyTreeFamilyTreesDemoGetLocale | Unset = GetDemoFamilyTreeFamilyTreesDemoGetLocale.EN,
) -> FamilyTreeResponse | HTTPValidationError | None:
    """The publicly readable demo tree for a UI locale

     Point a signed-out visitor at the demo tree for their language.

    Declared above `/{tree_id}` so the literal path wins the match, and the only
    route here that takes no credentials. `my_permissions` comes back as the
    read-only demo set, which is the same field the client already reads to
    decide what to render — so the demo needs no second rendering path.

    Args:
        locale (GetDemoFamilyTreeFamilyTreesDemoGetLocale | Unset): UI locale: `fa` and `en` may
            point at different demo trees. Default: GetDemoFamilyTreeFamilyTreesDemoGetLocale.EN.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FamilyTreeResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            locale=locale,
        )
    ).parsed
