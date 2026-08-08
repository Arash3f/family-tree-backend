from uuid import uuid4
from unittest.mock import MagicMock

import pytest

from app.application.use_cases.person.get_closest_relationship_use_case import (
    GetClosestRelationshipUseCase,
)
from app.domain.exceptions.person_exceptions import PersonNotFoundException
from app.domain.shared.dto.family_tree_dto import RelationshipPathDTO


def test_get_closest_relationship_success():
    from_id = uuid4()
    to_id = uuid4()
    repo = MagicMock()
    repo.person_exists.return_value = True
    repo.find_shortest_relationship_path.return_value = RelationshipPathDTO(
        from_person_id=from_id,
        to_person_id=to_id,
        found=True,
        distance=1,
        path_person_ids=[from_id, to_id],
        relationship_types=["PARENT_OF"],
    )

    result = GetClosestRelationshipUseCase(repo).execute(from_id, to_id)

    assert result.found is True
    assert result.distance == 1
    repo.find_shortest_relationship_path.assert_called_once_with(
        from_person_id=from_id, to_person_id=to_id
    )


def test_get_closest_relationship_missing_person():
    repo = MagicMock()
    repo.person_exists.return_value = False

    with pytest.raises(PersonNotFoundException):
        GetClosestRelationshipUseCase(repo).execute(uuid4(), uuid4())
