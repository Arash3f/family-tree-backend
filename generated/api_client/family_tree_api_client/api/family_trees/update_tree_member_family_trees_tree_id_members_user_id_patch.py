from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.tree_member_update_request import TreeMemberUpdateRequest
from ...models.tree_membership_response import TreeMembershipResponse
from ...types import Response


def _get_kwargs(
    tree_id: UUID,
    user_id: UUID,
    *,
    body: TreeMemberUpdateRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/family-trees/{tree_id}/members/{user_id}".format(
            tree_id=quote(str(tree_id), safe=""),
            user_id=quote(str(user_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TreeMembershipResponse | None:
    if response.status_code == 200:
        response_200 = TreeMembershipResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TreeMembershipResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    tree_id: UUID,
    user_id: UUID,
    *,
    client: AuthenticatedClient,
    body: TreeMemberUpdateRequest,
) -> Response[HTTPValidationError | TreeMembershipResponse]:
    """Update Tree Member

    Args:
        tree_id (UUID):
        user_id (UUID):
        body (TreeMemberUpdateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TreeMembershipResponse]
    """

    kwargs = _get_kwargs(
        tree_id=tree_id,
        user_id=user_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    tree_id: UUID,
    user_id: UUID,
    *,
    client: AuthenticatedClient,
    body: TreeMemberUpdateRequest,
) -> HTTPValidationError | TreeMembershipResponse | None:
    """Update Tree Member

    Args:
        tree_id (UUID):
        user_id (UUID):
        body (TreeMemberUpdateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TreeMembershipResponse
    """

    return sync_detailed(
        tree_id=tree_id,
        user_id=user_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    tree_id: UUID,
    user_id: UUID,
    *,
    client: AuthenticatedClient,
    body: TreeMemberUpdateRequest,
) -> Response[HTTPValidationError | TreeMembershipResponse]:
    """Update Tree Member

    Args:
        tree_id (UUID):
        user_id (UUID):
        body (TreeMemberUpdateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TreeMembershipResponse]
    """

    kwargs = _get_kwargs(
        tree_id=tree_id,
        user_id=user_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    tree_id: UUID,
    user_id: UUID,
    *,
    client: AuthenticatedClient,
    body: TreeMemberUpdateRequest,
) -> HTTPValidationError | TreeMembershipResponse | None:
    """Update Tree Member

    Args:
        tree_id (UUID):
        user_id (UUID):
        body (TreeMemberUpdateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TreeMembershipResponse
    """

    return (
        await asyncio_detailed(
            tree_id=tree_id,
            user_id=user_id,
            client=client,
            body=body,
        )
    ).parsed
