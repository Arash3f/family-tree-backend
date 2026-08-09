from datetime import date
from uuid import UUID

from app.application.dto.person.person_create_dto import PersonCreateMapper
from app.application.dto.person.person_get_dto import PersonGetMapper
from app.application.dto.person.person_update_dto import PersonUpdateMapper
from app.domain.entities.person import Gender, Person


TEST_TREE_ID = UUID(int=1)


def create_person(**overrides):
    return Person(
        id=overrides.get("id", UUID(int=1)),
        name=overrides.get("name", "Ali"),
        gender=overrides.get("gender", Gender.MALE),
        tree_id=overrides.get("tree_id", TEST_TREE_ID),
        birth_date=overrides.get("birth_date", date(2000, 1, 1)),
        parents=overrides.get("parents", []),
        marriage_id=overrides.get("marriage_id", None),
        photo_object_key=overrides.get("photo_object_key", None),
    )


def test_person_create_mapper_to_response():
    person = create_person()

    dto = PersonCreateMapper.to_response(person, photo_url="https://example/p")

    assert dto.id == person.id
    assert dto.name == person.name
    assert dto.gender == person.gender
    assert dto.birth_date == person.birth_date
    assert dto.parents == []
    assert dto.marriage_id is None
    assert dto.photo_object_key is None
    assert dto.photo_url == "https://example/p"


def test_person_get_mapper_to_response():
    person = create_person()

    dto = PersonGetMapper.to_response(person)

    assert dto.id == person.id
    assert dto.name == person.name
    assert dto.gender == person.gender
    assert dto.birth_date == person.birth_date
    assert dto.parents == []
    assert dto.photo_url is None


def test_person_update_mapper_to_response():
    person = create_person()

    dto = PersonUpdateMapper.to_response(person)

    assert dto.id == person.id
    assert dto.name == person.name
    assert dto.gender == person.gender
    assert dto.birth_date == person.birth_date
    assert dto.parents == []
    assert dto.photo_object_key is None
