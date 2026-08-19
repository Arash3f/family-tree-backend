import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from family_tree_api_client import AuthenticatedClient, Client
from family_tree_api_client.api.media.upload_media_family_trees_tree_id_media_upload_post import (  # noqa: E501
    asyncio_detailed as upload_media,
)
from family_tree_api_client.models.body_upload_media_family_trees_tree_id_media_upload_post import (  # noqa: E501
    BodyUploadMediaFamilyTreesTreeIdMediaUploadPost,
)
from family_tree_api_client.models.media_upload_response import MediaUploadResponse
from httpx import ASGITransport

from app.domain.shared.tree_access import TreeAccessPermissions
from app.main import app
from app.presentation.dependencies import get_person_photo_service
from app.utils.error_codes import ErrorCode
from tests.e2e.auth_headers import member_client as member_client
from tests.helpers.auth import create_authenticated_user
from tests.helpers.family_tree import add_tree_member


class _UploadMediaBody(BodyUploadMediaFamilyTreesTreeIdMediaUploadPost):
    def to_multipart(self):
        return [("file", (self.file_name, self.payload, self.mime_type))]


def _upload_body(payload: bytes, file_name: str, mime_type: str) -> _UploadMediaBody:
    body = _UploadMediaBody(file=file_name)
    body.file_name = file_name
    body.payload = payload
    body.mime_type = mime_type
    return body


@pytest.mark.asyncio
async def test_photo_upload_requires_tree_membership(
    tree_id, member_client: AuthenticatedClient
):
    response = await upload_media(
        tree_id=tree_id,
        client=member_client,
        body=_upload_body(b"\x89PNG\r\n\x1a\npayload", "photo.png", "image/png"),
    )

    assert response.status_code == 403
    assert json.loads(response.content)["error_code"] == int(
        ErrorCode.TREE_MEMBERSHIP_DENIED
    )


@pytest.mark.asyncio
async def test_photo_upload_requires_tree_capability(
    client: Client, tree_id, uow, asgi_transport: ASGITransport
):
    member = await create_authenticated_user(
        client, uow, permissions=[], asgi_transport=asgi_transport
    )
    await add_tree_member(uow, tree_id=tree_id, user_id=member.user.safe_id)
    await uow.commit()

    response = await upload_media(
        tree_id=tree_id,
        client=member.client,
        body=_upload_body(b"\x89PNG\r\n\x1a\npayload", "photo.png", "image/png"),
    )

    assert response.status_code == 403
    assert json.loads(response.content)["error_code"] == int(
        ErrorCode.TREE_ACCESS_DENIED
    )


@pytest.mark.asyncio
async def test_photo_upload_is_tree_scoped_without_system_rbac(
    client: Client, tree_id, uow, asgi_transport: ASGITransport
):
    member = await create_authenticated_user(
        client, uow, permissions=[], asgi_transport=asgi_transport
    )
    await add_tree_member(
        uow,
        tree_id=tree_id,
        user_id=member.user.safe_id,
        permissions=[TreeAccessPermissions.UPLOAD_PHOTO],
    )
    await uow.commit()

    photo_service = MagicMock()
    photo_service.upload_person_photo = AsyncMock(
        return_value="persons/11111111-1111-1111-1111-111111111111.png"
    )
    app.dependency_overrides[get_person_photo_service] = lambda: photo_service
    try:
        response = await upload_media(
            tree_id=tree_id,
            client=member.client,
            body=_upload_body(b"\x89PNG\r\n\x1a\npayload", "photo.png", "image/png"),
        )
    finally:
        app.dependency_overrides.pop(get_person_photo_service, None)

    assert response.status_code == 200
    assert isinstance(response.parsed, MediaUploadResponse)
    assert (
        response.parsed.object_key == "persons/11111111-1111-1111-1111-111111111111.png"
    )
    photo_service.upload_person_photo.assert_awaited_once_with(
        b"\x89PNG\r\n\x1a\npayload", "image/png"
    )
