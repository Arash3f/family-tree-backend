import pytest
from datetime import date

from app.application.dto.person.person_create_dto import PersonCreateMapper
from app.application.dto.person.person_get_dto import PersonGetMapper
from app.application.dto.person.person_update_dto import PersonUpdateMapper
from app.domain.entities.person import Person, Gender


def create_person(**kwargs):
    data = {
        "id": 1,
        "name": "Ali",
        "gender": Gender.MALE,
        "birth_date": date(2000, 1, 1),
        "father_id": 10,
        "mother_id": 20,
    }
    data.update(kwargs)
    return Person(**data)


def test_person_create_mapper_to_response():
    person = create_person()

    dto = PersonCreateMapper.to_response(person)

    assert dto.id == person.id
    assert dto.name == person.name
    assert dto.gender == person.gender
    assert dto.birth_date == person.birth_date
    assert dto.father_id == person.father_id
    assert dto.mother_id == person.mother_id


def test_person_get_mapper_to_response():
    person = create_person()

    dto = PersonGetMapper.to_response(person)

    assert dto.id == person.id
    assert dto.name == person.name
    assert dto.gender == person.gender
    assert dto.birth_date == person.birth_date
    assert dto.father_id == person.father_id
    assert dto.mother_id == person.mother_id


def test_person_update_mapper_to_response():
    person = create_person()

    dto = PersonUpdateMapper.to_response(person)

    assert dto.id == person.id
    assert dto.name == person.name
    assert dto.gender == person.gender
    assert dto.birth_date == person.birth_date
    assert dto.father_id == person.father_id
    assert dto.mother_id == person.mother_id


def test_person_mapper_raises_if_id_is_none():
    person = create_person(id=None)

    with pytest.raises(AssertionError):
        PersonCreateMapper.to_response(person)
