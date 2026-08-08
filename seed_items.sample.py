from datetime import date, datetime, timezone
from typing import NotRequired, TypedDict

from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.marriage import Marriage
from app.domain.entities.person import Gender, Person
from app.domain.shared.dto.family_tree_dto import (
    ParentRelationshipDTO,
    PersonUpsertDTO,
    SpouseRelationshipDTO,
)
from app.infrastructure.repositories.neo4j_family_tree_repository import (
    Neo4jFamilyTreeRepository,
)


class PersonSeedData(TypedDict):
    key: str
    name: str
    gender: Gender
    father: NotRequired[str]
    mother: NotRequired[str]


class MarriageSeedData(TypedDict):
    husband: str
    wife: str
    married_at: date


async def get_or_create_person(
    uow: UnitOfWork,
    person: Person,
    neo_repo: Neo4jFamilyTreeRepository,
) -> Person:
    now_utc = datetime.now(timezone.utc)
    created_at = None

    find_person = await uow.persons.get_by_name(
        name=person.name, father_id=person.father_id, mother_id=person.mother_id
    )

    if find_person:
        person.id = find_person.safe_id
        person = await uow.persons.update(person=person)
        created_at = now_utc

    else:
        person = await uow.persons.create(person=person)

    data: PersonUpsertDTO = PersonUpsertDTO(
        id=person.safe_id,
        full_name=person.name,
        gender=person.gender.name,
        birth_date=person.birth_date,
        death_date=None,
        created_at=created_at,
        updated_at=now_utc,
    )

    neo_repo.upsert_person(data)

    if person.father_id:
        neo_repo.create_parent_relationship(
            data=ParentRelationshipDTO(
                child_id=person.safe_id,
                parent_id=person.father_id,
            )
        )

    if person.mother_id:
        neo_repo.create_parent_relationship(
            data=ParentRelationshipDTO(
                child_id=person.safe_id,
                parent_id=person.mother_id,
            )
        )

    await uow.commit()
    return person


async def get_or_create_marriage(
    uow: UnitOfWork,
    marriage: Marriage,
    neo_repo: Neo4jFamilyTreeRepository,
) -> Marriage:
    find_marriage = await uow.marriages.get_by_ids(
        husband_id=marriage.husband_id,
        wife_id=marriage.wife_id,
    )

    if find_marriage:
        marriage.id = find_marriage.id
        marriage = await uow.marriages.update(marriage=marriage)
    else:
        marriage = await uow.marriages.create(marriage=marriage)

    neo_repo.create_spouse_relationship(
        data=SpouseRelationshipDTO(
            person_id_1=marriage.husband_id,
            person_id_2=marriage.wife_id,
        )
    )

    await uow.commit()
    return marriage


SEED_PEOPLE: list[PersonSeedData] = [
    {
        "key": "arash_alfooneh",
        "name": "آرش الفونه",
        "gender": Gender.MALE,
    },
    {
        "key": "roz_ebrahimi",
        "name": "رز ابراهیمی",
        "gender": Gender.FEMALE,
    },
    {
        "key": "mani_alfooneh",
        "name": "مانی الفونه",
        "gender": Gender.MALE,
        "father": "arash_alfooneh",
        "mother": "roz_ebrahimi",
    },
]

SEED_MARRIAGES: list[MarriageSeedData] = [
    {
        "husband": "arash_alfooneh",
        "wife": "roz_ebrahimi",
        "married_at": date(2000, 1, 1),
    },
]


async def seed_initial_items(uow: UnitOfWork):
    people_map: dict[str, Person] = {}
    neo_repo = Neo4jFamilyTreeRepository()

    async with uow:
        for item in SEED_PEOPLE:
            father_key = item.get("father")
            mother_key = item.get("mother")

            father_id = people_map[father_key].safe_id if father_key else None
            mother_id = people_map[mother_key].safe_id if mother_key else None

            person = await get_or_create_person(
                uow=uow,
                person=Person(
                    id=None,
                    name=item["name"],
                    gender=item["gender"],
                    birth_date=None,
                    father_id=father_id,
                    mother_id=mother_id,
                ),
                neo_repo=neo_repo,
            )

            people_map[item["key"]] = person

        for marriage_item in SEED_MARRIAGES:
            husband_node = people_map[marriage_item["husband"]]
            wife_node = people_map[marriage_item["wife"]]

            await get_or_create_marriage(
                uow=uow,
                marriage=Marriage(
                    id=None,
                    husband_id=husband_node.safe_id,
                    wife_id=wife_node.safe_id,
                    married_at=marriage_item["married_at"],
                    divorced_at=None,
                ),
                neo_repo=neo_repo,
            )
