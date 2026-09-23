from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.family_tree_response import FamilyTreeResponse
from ...types import Response


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/family-trees/demo",
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> FamilyTreeResponse | None:
    if response.status_code == 200:
        response_200 = FamilyTreeResponse.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[FamilyTreeResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[FamilyTreeResponse]:
    """The publicly readable demo tree

     Point a signed-out visitor at the demo tree.

    Declared above `/{tree_id}` so the literal path wins the match, and the only
    route here that takes no credentials. `my_permissions` comes back as the
    read-only demo set, which is the same field the client already reads to
    decide what to render — so the demo needs no second rendering path.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FamilyTreeResponse]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> FamilyTreeResponse | None:
    """The publicly readable demo tree

     Point a signed-out visitor at the demo tree.

    Declared above `/{tree_id}` so the literal path wins the match, and the only
    route here that takes no credentials. `my_permissions` comes back as the
    read-only demo set, which is the same field the client already reads to
    decide what to render — so the demo needs no second rendering path.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FamilyTreeResponse
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[FamilyTreeResponse]:
    """The publicly readable demo tree

     Point a signed-out visitor at the demo tree.

    Declared above `/{tree_id}` so the literal path wins the match, and the only
    route here that takes no credentials. `my_permissions` comes back as the
    read-only demo set, which is the same field the client already reads to
    decide what to render — so the demo needs no second rendering path.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FamilyTreeResponse]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> FamilyTreeResponse | None:
    """The publicly readable demo tree

     Point a signed-out visitor at the demo tree.

    Declared above `/{tree_id}` so the literal path wins the match, and the only
    route here that takes no credentials. `my_permissions` comes back as the
    read-only demo set, which is the same field the client already reads to
    decide what to render — so the demo needs no second rendering path.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FamilyTreeResponse
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
