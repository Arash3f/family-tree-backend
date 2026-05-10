from datetime import date, datetime, timezone

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
                child_id=person.safe_id, parent_id=person.father_id
            )
        )
    if person.mother_id:
        neo_repo.create_parent_relationship(
            data=ParentRelationshipDTO(
                child_id=person.safe_id, parent_id=person.mother_id
            )
        )

    await uow.commit()

    return person


async def get_or_create_marriage(
    uow: UnitOfWork, marriage: Marriage, neo_repo: Neo4jFamilyTreeRepository
) -> Marriage:
    find_marriage = await uow.marriages.get_by_ids(
        husband_id=marriage.husband_id, wife_id=marriage.wife_id
    )
    if find_marriage:
        marriage.id = find_marriage.id
        marriage = await uow.marriages.update(marriage=marriage)
    else:
        marriage = await uow.marriages.create(marriage=marriage)

    neo_repo.create_spouse_relationship(
        data=SpouseRelationshipDTO(
            person_id_1=marriage.husband_id, person_id_2=marriage.wife_id
        )
    )

    await uow.commit()

    return marriage


SEED_PEOPLE = [
    {
        "key": "arash_alfooneh",  # ! Unique
        "name": "آرش الفونه",
        "gender": Gender.MALE,
    },
    {
        "key": "roz_ebrahimi",  # ! Unique
        "name": "رز ابراهیمی",
        "gender": Gender.FEMALE,
    },
    {
        "key": "mani_alfooneh",  # ! Unique
        "name": "مانی الفونه",
        "gender": Gender.MALE,
        "father": "arash_alfooneh",
        "mother": "roz_ebrahimi",
    },
]

SEED_MARRIAGES = [
    {
        "husband": "arash_alfooneh",
        "wife": "roz_ebrahimi",
        "married_at": date(2000, 1, 1),
    },
]


async def seed_initial_items(uow: UnitOfWork):
    neo_repo = Neo4jFamilyTreeRepository()

    people_map = {}

    async with uow:
        for item in SEED_PEOPLE:
            father_id = (
                people_map[item["father"]].safe_id if item.get("father") else None
            )

            mother_id = (
                people_map[item["mother"]].safe_id if item.get("mother") else None
            )

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

        for marriage in SEED_MARRIAGES:
            await get_or_create_marriage(
                uow=uow,
                marriage=Marriage(
                    id=None,
                    husband_id=people_map[marriage["husband"]].safe_id,
                    wife_id=people_map[marriage["wife"]].safe_id,
                    married_at=marriage["married_at"],
                    divorced_at=None,
                ),
                neo_repo=neo_repo,
            )
