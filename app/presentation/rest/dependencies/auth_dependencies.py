from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.application.interfaces.unit_of_work import UnitOfWork
from app.core.config import settings
from app.domain.exceptions.auth_exceptions import InvalidCredentialsException
from app.domain.exceptions.user_exceptions import UserNotFoundException
from app.presentation.rest.utils.dependencies import get_uow

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    uow: UnitOfWork = Depends(get_uow),
):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )

        user_id: int | None = payload.get("sub")

        if user_id is None:
            raise InvalidCredentialsException()

    except JWTError:
        raise InvalidCredentialsException()

    async with uow:
        user = await uow.users.get(int(user_id))

        if not user:
            raise UserNotFoundException()

        return user
