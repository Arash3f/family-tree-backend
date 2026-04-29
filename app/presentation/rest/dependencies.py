from fastapi import Depends

from app.application.use_cases.person.create_person_use_case import CreatePersonUseCase
from app.domain.services.marriage_rules import MarriageRulesService
from app.infrastructure.database.session import async_session
from app.infrastructure.unit_of_work.sqlalchemy_uow import SQLAlchemyUnitOfWork


def get_uow():
    return SQLAlchemyUnitOfWork(async_session)


def get_create_person_usecase(uow=Depends(get_uow)):
    return CreatePersonUseCase(uow)


def get_marriage_rules_service() -> MarriageRulesService:
    return MarriageRulesService()


def get_marriage_rule_service(
    rules_service: MarriageRulesService = Depends(get_marriage_rules_service),
) -> MarriageRulesService:
    return rules_service
