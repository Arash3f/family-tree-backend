from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.closest_relationship_response import ClosestRelationshipResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    tree_id: UUID,
    from_person_id: UUID,
    to_person_id: UUID,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/family-trees/{tree_id}/persons/{from_person_id}/relation/{to_person_id}".format(
            tree_id=quote(str(tree_id), safe=""),
            from_person_id=quote(str(from_person_id), safe=""),
            to_person_id=quote(str(to_person_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ClosestRelationshipResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = ClosestRelationshipResponse.from_dict(response.json())

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
) -> Response[ClosestRelationshipResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    tree_id: UUID,
    from_person_id: UUID,
    to_person_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[ClosestRelationshipResponse | HTTPValidationError]:
    """Get Closest Relationship

    Args:
        tree_id (UUID):
        from_person_id (UUID):
        to_person_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ClosestRelationshipResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        tree_id=tree_id,
        from_person_id=from_person_id,
        to_person_id=to_person_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    tree_id: UUID,
    from_person_id: UUID,
    to_person_id: UUID,
    *,
    client: AuthenticatedClient,
) -> ClosestRelationshipResponse | HTTPValidationError | None:
    """Get Closest Relationship

    Args:
        tree_id (UUID):
        from_person_id (UUID):
        to_person_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ClosestRelationshipResponse | HTTPValidationError
    """

    return sync_detailed(
        tree_id=tree_id,
        from_person_id=from_person_id,
        to_person_id=to_person_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    tree_id: UUID,
    from_person_id: UUID,
    to_person_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[ClosestRelationshipResponse | HTTPValidationError]:
    """Get Closest Relationship

    Args:
        tree_id (UUID):
        from_person_id (UUID):
        to_person_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ClosestRelationshipResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        tree_id=tree_id,
        from_person_id=from_person_id,
        to_person_id=to_person_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    tree_id: UUID,
    from_person_id: UUID,
    to_person_id: UUID,
    *,
    client: AuthenticatedClient,
) -> ClosestRelationshipResponse | HTTPValidationError | None:
    """Get Closest Relationship

    Args:
        tree_id (UUID):
        from_person_id (UUID):
        to_person_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ClosestRelationshipResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            tree_id=tree_id,
            from_person_id=from_person_id,
            to_person_id=to_person_id,
            client=client,
        )
    ).parsed
