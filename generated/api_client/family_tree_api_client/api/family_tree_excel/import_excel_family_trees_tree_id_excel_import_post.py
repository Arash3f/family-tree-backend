from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.body_import_excel_family_trees_tree_id_excel_import_post import (
    BodyImportExcelFamilyTreesTreeIdExcelImportPost,
)
from ...models.http_validation_error import HTTPValidationError
from ...models.tree_excel_import_response import TreeExcelImportResponse
from ...types import Response


def _get_kwargs(
    tree_id: UUID,
    *,
    body: BodyImportExcelFamilyTreesTreeIdExcelImportPost,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/family-trees/{tree_id}/excel/import".format(
            tree_id=quote(str(tree_id), safe=""),
        ),
    }

    _kwargs["files"] = body.to_multipart()

    headers["Content-Type"] = "multipart/form-data; boundary=+++"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TreeExcelImportResponse | None:
    if response.status_code == 200:
        response_200 = TreeExcelImportResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TreeExcelImportResponse]:
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
    body: BodyImportExcelFamilyTreesTreeIdExcelImportPost,
) -> Response[HTTPValidationError | TreeExcelImportResponse]:
    """Import Excel

    Args:
        tree_id (UUID):
        body (BodyImportExcelFamilyTreesTreeIdExcelImportPost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TreeExcelImportResponse]
    """

    kwargs = _get_kwargs(
        tree_id=tree_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    tree_id: UUID,
    *,
    client: AuthenticatedClient,
    body: BodyImportExcelFamilyTreesTreeIdExcelImportPost,
) -> HTTPValidationError | TreeExcelImportResponse | None:
    """Import Excel

    Args:
        tree_id (UUID):
        body (BodyImportExcelFamilyTreesTreeIdExcelImportPost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TreeExcelImportResponse
    """

    return sync_detailed(
        tree_id=tree_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    tree_id: UUID,
    *,
    client: AuthenticatedClient,
    body: BodyImportExcelFamilyTreesTreeIdExcelImportPost,
) -> Response[HTTPValidationError | TreeExcelImportResponse]:
    """Import Excel

    Args:
        tree_id (UUID):
        body (BodyImportExcelFamilyTreesTreeIdExcelImportPost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TreeExcelImportResponse]
    """

    kwargs = _get_kwargs(
        tree_id=tree_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    tree_id: UUID,
    *,
    client: AuthenticatedClient,
    body: BodyImportExcelFamilyTreesTreeIdExcelImportPost,
) -> HTTPValidationError | TreeExcelImportResponse | None:
    """Import Excel

    Args:
        tree_id (UUID):
        body (BodyImportExcelFamilyTreesTreeIdExcelImportPost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TreeExcelImportResponse
    """

    return (
        await asyncio_detailed(
            tree_id=tree_id,
            client=client,
            body=body,
        )
    ).parsed
