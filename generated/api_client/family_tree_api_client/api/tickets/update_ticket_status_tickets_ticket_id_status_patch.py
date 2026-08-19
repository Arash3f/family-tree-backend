from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.ticket_update_status_request import TicketUpdateStatusRequest
from ...models.ticket_update_status_response import TicketUpdateStatusResponse
from ...types import Response


def _get_kwargs(
    ticket_id: UUID,
    *,
    body: TicketUpdateStatusRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/tickets/{ticket_id}/status".format(
            ticket_id=quote(str(ticket_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TicketUpdateStatusResponse | None:
    if response.status_code == 200:
        response_200 = TicketUpdateStatusResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TicketUpdateStatusResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    ticket_id: UUID,
    *,
    client: AuthenticatedClient,
    body: TicketUpdateStatusRequest,
) -> Response[HTTPValidationError | TicketUpdateStatusResponse]:
    """Update Ticket Status

    Args:
        ticket_id (UUID):
        body (TicketUpdateStatusRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TicketUpdateStatusResponse]
    """

    kwargs = _get_kwargs(
        ticket_id=ticket_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    ticket_id: UUID,
    *,
    client: AuthenticatedClient,
    body: TicketUpdateStatusRequest,
) -> HTTPValidationError | TicketUpdateStatusResponse | None:
    """Update Ticket Status

    Args:
        ticket_id (UUID):
        body (TicketUpdateStatusRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TicketUpdateStatusResponse
    """

    return sync_detailed(
        ticket_id=ticket_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    ticket_id: UUID,
    *,
    client: AuthenticatedClient,
    body: TicketUpdateStatusRequest,
) -> Response[HTTPValidationError | TicketUpdateStatusResponse]:
    """Update Ticket Status

    Args:
        ticket_id (UUID):
        body (TicketUpdateStatusRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TicketUpdateStatusResponse]
    """

    kwargs = _get_kwargs(
        ticket_id=ticket_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    ticket_id: UUID,
    *,
    client: AuthenticatedClient,
    body: TicketUpdateStatusRequest,
) -> HTTPValidationError | TicketUpdateStatusResponse | None:
    """Update Ticket Status

    Args:
        ticket_id (UUID):
        body (TicketUpdateStatusRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TicketUpdateStatusResponse
    """

    return (
        await asyncio_detailed(
            ticket_id=ticket_id,
            client=client,
            body=body,
        )
    ).parsed
