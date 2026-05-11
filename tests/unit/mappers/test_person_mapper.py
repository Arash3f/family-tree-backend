from datetime import date

from app.application.dto.person.person_create_dto import PersonCreateMapper
from app.application.dto.person.person_get_dto import PersonGetMapper
from app.application.dto.person.person_update_dto import PersonUpdateMapper
from app.domain.entities.person import Gender, Person


def create_person(**overrides):
    return Person(
        id=overrides.get("id", 1),
        name=overrides.get("name", "Ali"),
        gender=overrides.get("gender", Gender.MALE),
        birth_date=overrides.get("birth_date", date(2000, 1, 1)),
        father_id=overrides.get("father_id", 10),
        mother_id=overrides.get("mother_id", 20),
    )


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
