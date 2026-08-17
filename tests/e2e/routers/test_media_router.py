from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.shared.tree_access import TreeAccessPermissions
from app.main import app
from app.presentation.rest.utils.dependencies import get_person_photo_service
from app.utils.error_codes import ErrorCode
from tests.e2e.auth_headers import member_headers as member_headers
from tests.helpers.auth import create_authenticated_user
from tests.helpers.family_tree import add_tree_member


def upload_url(tree_id) -> str:
    return f"/family-trees/{tree_id}/media/upload"


@pytest.mark.asyncio
async def test_photo_upload_requires_tree_membership(client, tree_id, member_headers):  # noqa: F811
    response = await client.post(
        upload_url(tree_id),
        files={"file": ("photo.png", b"\x89PNG\r\n\x1a\npayload", "image/png")},
        headers=member_headers,
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)


@pytest.mark.asyncio
async def test_photo_upload_requires_tree_capability(client, tree_id, uow):
    member = await create_authenticated_user(client, uow, permissions=[])
    await add_tree_member(uow, tree_id=tree_id, user_id=member.user.safe_id)
    await uow.commit()

    response = await client.post(
        upload_url(tree_id),
        files={"file": ("photo.png", b"\x89PNG\r\n\x1a\npayload", "image/png")},
        headers=member.headers,
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == int(ErrorCode.TREE_ACCESS_DENIED)


@pytest.mark.asyncio
async def test_photo_upload_is_tree_scoped_without_system_rbac(client, tree_id, uow):
    member = await create_authenticated_user(client, uow, permissions=[])
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
        response = await client.post(
            upload_url(tree_id),
            files={"file": ("photo.png", b"\x89PNG\r\n\x1a\npayload", "image/png")},
            headers=member.headers,
        )
    finally:
        app.dependency_overrides.pop(get_person_photo_service, None)

    assert response.status_code == 200
    assert response.json() == {
        "object_key": "persons/11111111-1111-1111-1111-111111111111.png"
    }
    photo_service.upload_person_photo.assert_awaited_once_with(
        b"\x89PNG\r\n\x1a\npayload", "image/png"
    )
