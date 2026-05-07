from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.application.dto.auth_dto import LoginDTO
from app.application.use_cases.login_user import LoginUserUseCase
from app.presentation.rest.utils.dependencies import (
    get_password_hasher,
    get_token_service,
    get_uow,
)
from app.presentation.rest.schemas.dto.auth_schema import LoginResponse
from app.presentation.rest.schemas.mappers.auth_mappers import AuthApiMapper

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    uow=Depends(get_uow),
    token_service=Depends(get_token_service),
    password_hasher=Depends(get_password_hasher),
) -> LoginResponse:
    data = LoginDTO(
        password=form_data.password,
        username=form_data.username,
    )
    usecase = LoginUserUseCase(uow, password_hasher, token_service)

    tokens = await usecase.execute(data)

    return AuthApiMapper.from_login_dto(tokens)
