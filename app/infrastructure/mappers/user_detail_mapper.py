from app.domain.shared.account_type import AccountType
from app.domain.shared.dto.user_with_detail_dto import (
    UserGetWithDetailResponseDTO,
    _Permission,
    _RoleData,
)
from app.domain.shared.user_preferences import PreferredLocale, PreferredTheme
from app.infrastructure.database.models.user_model import UserModel


def user_model_to_detail_dto(model: UserModel) -> UserGetWithDetailResponseDTO:
    role = None
    if model.role:
        role = _RoleData(
            id=model.role.id,
            name=model.role.name,
            permissions=[
                _Permission(
                    id=p.id,
                    name=p.name,
                    description_en=getattr(p, "description_en", "") or "",
                    description_fa=getattr(p, "description_fa", "") or "",
                )
                for p in model.role.permissions
            ],
        )

    return UserGetWithDetailResponseDTO(
        id=model.id,
        username=model.username,
        fullname=model.fullname,
        email=model.email,
        phone=model.phone,
        role_id=model.role_id,
        account_type=AccountType(model.account_type),
        is_active=model.is_active,
        preferred_locale=(
            PreferredLocale(model.preferred_locale) if model.preferred_locale else None
        ),
        preferred_theme=(
            PreferredTheme(model.preferred_theme) if model.preferred_theme else None
        ),
        role=role,
    )
