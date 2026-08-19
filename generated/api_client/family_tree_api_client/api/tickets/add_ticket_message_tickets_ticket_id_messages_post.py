from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.ticket_message_create_request import TicketMessageCreateRequest
from ...models.ticket_message_create_response import TicketMessageCreateResponse
from ...types import Response


def _get_kwargs(
    ticket_id: UUID,
    *,
    body: TicketMessageCreateRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/tickets/{ticket_id}/messages".format(
            ticket_id=quote(str(ticket_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TicketMessageCreateResponse | None:
    if response.status_code == 201:
        response_201 = TicketMessageCreateResponse.from_dict(response.json())

        return response_201

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | TicketMessageCreateResponse]:
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
    body: TicketMessageCreateRequest,
) -> Response[HTTPValidationError | TicketMessageCreateResponse]:
    """Add Ticket Message

    Args:
        ticket_id (UUID):
        body (TicketMessageCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TicketMessageCreateResponse]
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
    body: TicketMessageCreateRequest,
) -> HTTPValidationError | TicketMessageCreateResponse | None:
    """Add Ticket Message

    Args:
        ticket_id (UUID):
        body (TicketMessageCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TicketMessageCreateResponse
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
    body: TicketMessageCreateRequest,
) -> Response[HTTPValidationError | TicketMessageCreateResponse]:
    """Add Ticket Message

    Args:
        ticket_id (UUID):
        body (TicketMessageCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TicketMessageCreateResponse]
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
    body: TicketMessageCreateRequest,
) -> HTTPValidationError | TicketMessageCreateResponse | None:
    """Add Ticket Message

    Args:
        ticket_id (UUID):
        body (TicketMessageCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TicketMessageCreateResponse
    """

    return (
        await asyncio_detailed(
            ticket_id=ticket_id,
            client=client,
            body=body,
        )
    ).parsed
