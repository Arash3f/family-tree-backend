from uuid import UUID, uuid4
from unittest.mock import MagicMock

import pytest

from app.domain.shared.dto.family_tree_dto import RelationshipPathDTO
from app.main import app
from app.presentation.rest.utils.dependencies import get_neo
from app.utils.error_codes import ERROR_MESSAGES, ErrorCode
from tests.e2e.auth_headers import admin_headers as admin_headers
from tests.e2e.auth_headers import member_headers as member_headers


def persons_url(tree_id: UUID, suffix: str = "") -> str:
    return f"/family-trees/{tree_id}/persons{suffix}"


@pytest.fixture
def mock_neo():
    repo = MagicMock()
    original = app.dependency_overrides.get(get_neo)
    app.dependency_overrides[get_neo] = lambda: repo
    yield repo
    if original is None:
        app.dependency_overrides.pop(get_neo, None)
    else:
        app.dependency_overrides[get_neo] = original


@pytest.mark.asyncio
async def test_closest_relationship_permission_denied(
    client, tree_id, member_headers, mock_neo  # noqa: F811
):
    from_id, to_id = uuid4(), uuid4()
    resp = await client.get(
        persons_url(tree_id, f"/{from_id}/relation/{to_id}"),
        headers=member_headers,
    )
    assert resp.status_code == 403
    body = resp.json()
    assert body["error_code"] == 1301
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]
    mock_neo.find_shortest_relationship_path.assert_not_called()


@pytest.mark.asyncio
async def test_closest_relationship_unauthenticated(client, tree_id, mock_neo):
    resp = await client.get(persons_url(tree_id, f"/{uuid4()}/relation/{uuid4()}"))
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_closest_relationship_success(
    client, tree_id, admin_headers, mock_neo  # noqa: F811
):
    from_id, to_id, mid = uuid4(), uuid4(), uuid4()
    mock_neo.person_exists.return_value = True
    mock_neo.find_shortest_relationship_path.return_value = RelationshipPathDTO(
        from_person_id=from_id,
        to_person_id=to_id,
        found=True,
        distance=2,
        path_person_ids=[from_id, mid, to_id],
        relationship_types=["PARENT_OF", "PARENT_OF"],
    )

    resp = await client.get(
        persons_url(tree_id, f"/{from_id}/relation/{to_id}"),
        headers=admin_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["found"] is True
    assert body["distance"] == 2
    assert body["from_person_id"] == str(from_id)
    assert body["to_person_id"] == str(to_id)
    assert body["path_person_ids"] == [str(from_id), str(mid), str(to_id)]
    assert body["relationship_types"] == ["PARENT_OF", "PARENT_OF"]


@pytest.mark.asyncio
async def test_closest_relationship_person_missing(
    client, tree_id, admin_headers, mock_neo  # noqa: F811
):
    from_id, to_id = uuid4(), uuid4()
    mock_neo.person_exists.return_value = False

    resp = await client.get(
        persons_url(tree_id, f"/{from_id}/relation/{to_id}"),
        headers=admin_headers,
    )
    assert resp.status_code == 404
    assert resp.json()["error_code"] == int(ErrorCode.PERSON_NOT_FOUND)
