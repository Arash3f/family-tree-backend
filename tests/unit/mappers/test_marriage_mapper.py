from datetime import date

from app.application.dto.marriage.marriage_create_dto import MarriageCreateMapper
from app.application.dto.marriage.marriage_get_dto import MarriageGetMapper
from app.application.dto.marriage.marriage_update_dto import MarriageUpdateDTOMapper
from app.domain.entities.marriage import Marriage


def create_marriage(**overrides):
    return Marriage(
        id=overrides.get("id", 1),
        husband_id=overrides.get("husband_id", 10),
        wife_id=overrides.get("wife_id", 20),
        married_at=overrides.get("married_at", date(2020, 1, 1)),
        divorced_at=overrides.get("divorced_at", None),
    )


def test_create_mapper_to_response():
    marriage = create_marriage()

    dto = MarriageCreateMapper.to_response(marriage)

    assert dto.id == marriage.id
    assert dto.husband_id == marriage.husband_id
    assert dto.wife_id == marriage.wife_id
    assert dto.married_at == marriage.married_at
    assert dto.divorced_at == marriage.divorced_at


def test_get_mapper_to_response():
    marriage = create_marriage()

    dto = MarriageGetMapper.to_response(marriage)

    assert dto.id == marriage.id
    assert dto.husband_id == marriage.husband_id
    assert dto.wife_id == marriage.wife_id
    assert dto.married_at == marriage.married_at
    assert dto.divorced_at == marriage.divorced_at


def test_update_mapper_to_response():
    marriage = create_marriage()

    dto = MarriageUpdateDTOMapper.to_response(marriage)

    assert dto.id == marriage.id
    assert dto.husband_id == marriage.husband_id
    assert dto.wife_id == marriage.wife_id
    assert dto.married_at == marriage.married_at
    assert dto.divorced_at == marriage.divorced_at
