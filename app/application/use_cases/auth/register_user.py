from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.application.dto.auth_dto import LoginResponseDTO, RegisterDTO
from app.application.interfaces.token_service import TokenService
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.starter_tree_provisioner import StarterTreeProvisioner
from app.core.config import settings
from app.domain.entities.user import User
from app.domain.entities.user_session import UserSession
from app.domain.exceptions.role_exceptions import RoleNotFoundException
from app.domain.exceptions.user_exceptions import (
    EmailAlreadyExistsException,
    PasswordConfirmationMismatchException,
    UsernameAlreadyExistsException,
)
from app.domain.services.password_hasher import PasswordHasher
from app.domain.shared.account_type import AccountType


def normalize_register_email(email: str | None) -> str | None:
    if email is None:
        return None
    cleaned = email.strip().lower()
    return cleaned or None


def normalize_register_phone(phone: str | None, country_code: str | None) -> str | None:
    """Combine country code + national number into a compact international form."""
    if phone is None:
        return None
    digits = "".join(ch for ch in phone if ch.isdigit())
    if not digits:
        return None

    code = (country_code or "").strip()
    if not code:
        return digits

    code = code if code.startswith("+") else f"+{code.lstrip('+')}"
    return f"{code}{digits.lstrip('0') or digits}"


class RegisterUserUseCase:
    """Public self-signup: free account with Member role, starter trees, then login."""

    def __init__(
        self,
        uow: UnitOfWork,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        starter_tree_provisioner: StarterTreeProvisioner | None = None,
    ):
        self.uow = uow
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.starter_tree_provisioner = (
            starter_tree_provisioner or StarterTreeProvisioner()
        )

    async def execute(
        self,
        data: RegisterDTO,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> LoginResponseDTO:
        if data.password != data.re_password:
            raise PasswordConfirmationMismatchException()

        email = normalize_register_email(data.email)
        phone = normalize_register_phone(data.phone, data.country_code)

        async with self.uow:
            if await self.uow.users.get_by_username(data.username):
                raise UsernameAlreadyExistsException()

            if email is not None and await self.uow.users.get_by_email(email):
                raise EmailAlreadyExistsException()

            member_role = await self.uow.roles.get_by_name(settings.MEMBER_ROLE_NAME)
            if member_role is None:
                raise RoleNotFoundException(
                    detail=[f"registration role {settings.MEMBER_ROLE_NAME!r} missing"]
                )

            user = await self.uow.users.create(
                User(
                    username=data.username,
                    password_hash=self.password_hasher.hash(data.password),
                    email=email,
                    phone=phone,
                    role_id=member_role.safe_id,
                    account_type=AccountType.FREE,
                )
            )

            starter_trees = await self.starter_tree_provisioner.provision_for_user(
                self.uow, owner_user_id=user.safe_id
            )

            session_id = uuid4()
            expires_at = datetime.now(UTC) + timedelta(
                minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
            )
            access = self.token_service.create_access_token(user.safe_id, session_id)
            refresh = self.token_service.create_refresh_token(user.safe_id, session_id)

            await self.uow.sessions.create(
                UserSession(
                    id=session_id,
                    user_id=user.safe_id,
                    refresh_token_hash=self.token_service.hash_token(refresh),
                    expires_at=expires_at,
                    user_agent=user_agent,
                    ip_address=ip_address,
                )
            )
            await self.uow.commit()

            self.starter_tree_provisioner.sync_after_commit(starter_trees)
            return LoginResponseDTO(access_token=access, refresh_token=refresh)
