from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.kinship_label_request import KinshipLabelRequest
from ...models.kinship_label_response import KinshipLabelResponse
from ...types import Response


def _get_kwargs(
    *,
    body: KinshipLabelRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/kinship/label",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | KinshipLabelResponse | None:
    if response.status_code == 200:
        response_200 = KinshipLabelResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | KinshipLabelResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: KinshipLabelRequest,
) -> Response[HTTPValidationError | KinshipLabelResponse]:
    """Name a relation given as a chain of family steps

     Public and stateless: no account, no tree, nothing stored. Uses the same labeller as the
    relationship finder, so the names match the app.

    Args:
        body (KinshipLabelRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | KinshipLabelResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: KinshipLabelRequest,
) -> HTTPValidationError | KinshipLabelResponse | None:
    """Name a relation given as a chain of family steps

     Public and stateless: no account, no tree, nothing stored. Uses the same labeller as the
    relationship finder, so the names match the app.

    Args:
        body (KinshipLabelRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | KinshipLabelResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: KinshipLabelRequest,
) -> Response[HTTPValidationError | KinshipLabelResponse]:
    """Name a relation given as a chain of family steps

     Public and stateless: no account, no tree, nothing stored. Uses the same labeller as the
    relationship finder, so the names match the app.

    Args:
        body (KinshipLabelRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | KinshipLabelResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: KinshipLabelRequest,
) -> HTTPValidationError | KinshipLabelResponse | None:
    """Name a relation given as a chain of family steps

     Public and stateless: no account, no tree, nothing stored. Uses the same labeller as the
    relationship finder, so the names match the app.

    Args:
        body (KinshipLabelRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | KinshipLabelResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
