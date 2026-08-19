from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.tree_membership_response import TreeMembershipResponse
from ...types import Response


def _get_kwargs(
    tree_id: UUID,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/family-trees/{tree_id}/members".format(
            tree_id=quote(str(tree_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list[TreeMembershipResponse] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = TreeMembershipResponse.from_dict(response_200_item_data)

            response_200.append(response_200_item)

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
) -> Response[HTTPValidationError | list[TreeMembershipResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    tree_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[HTTPValidationError | list[TreeMembershipResponse]]:
    """List Tree Members

    Args:
        tree_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[TreeMembershipResponse]]
    """

    kwargs = _get_kwargs(
        tree_id=tree_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    tree_id: UUID,
    *,
    client: AuthenticatedClient,
) -> HTTPValidationError | list[TreeMembershipResponse] | None:
    """List Tree Members

    Args:
        tree_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[TreeMembershipResponse]
    """

    return sync_detailed(
        tree_id=tree_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    tree_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[HTTPValidationError | list[TreeMembershipResponse]]:
    """List Tree Members

    Args:
        tree_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[TreeMembershipResponse]]
    """

    kwargs = _get_kwargs(
        tree_id=tree_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    tree_id: UUID,
    *,
    client: AuthenticatedClient,
) -> HTTPValidationError | list[TreeMembershipResponse] | None:
    """List Tree Members

    Args:
        tree_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[TreeMembershipResponse]
    """

    return (
        await asyncio_detailed(
            tree_id=tree_id,
            client=client,
        )
    ).parsed
