from datetime import date
from uuid import UUID

from app.application.dto.marriage.marriage_create_dto import MarriageCreateMapper
from app.application.dto.marriage.marriage_get_dto import MarriageGetMapper
from app.application.dto.marriage.marriage_update_dto import MarriageUpdateDTOMapper
from app.domain.entities.marriage import Marriage

TEST_TREE_ID = UUID(int=1)


def create_marriage(**overrides):
    return Marriage(
        id=overrides.get("id", UUID(int=1)),
        tree_id=overrides.get("tree_id", TEST_TREE_ID),
        spouse_a_id=overrides.get("spouse_a_id", UUID(int=10)),
        spouse_b_id=overrides.get("spouse_b_id", UUID(int=20)),
        married_at=overrides.get("married_at", date(2020, 1, 1)),
        divorced_at=overrides.get("divorced_at"),
    )


def test_create_mapper_to_response():
    marriage = create_marriage()

    dto = MarriageCreateMapper.to_response(marriage)

    assert dto.id == marriage.id
    assert dto.spouse_a_id == marriage.spouse_a_id
    assert dto.spouse_b_id == marriage.spouse_b_id
    assert dto.married_at == marriage.married_at
    assert dto.divorced_at == marriage.divorced_at


def test_get_mapper_to_response():
    marriage = create_marriage()

    dto = MarriageGetMapper.to_response(marriage)

    assert dto.id == marriage.id
    assert dto.spouse_a_id == marriage.spouse_a_id
    assert dto.spouse_b_id == marriage.spouse_b_id
    assert dto.married_at == marriage.married_at
    assert dto.divorced_at == marriage.divorced_at


def test_update_mapper_to_response():
    marriage = create_marriage()

    dto = MarriageUpdateDTOMapper.to_response(marriage)

    assert dto.id == marriage.id
    assert dto.spouse_a_id == marriage.spouse_a_id
    assert dto.spouse_b_id == marriage.spouse_b_id
    assert dto.married_at == marriage.married_at
    assert dto.divorced_at == marriage.divorced_at
