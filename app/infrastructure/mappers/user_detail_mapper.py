from app.domain.shared.account_type import AccountType
from app.domain.shared.dto.user_with_detail_dto import (
    UserGetWithDetailResponseDTO,
    _Permission,
    _RoleData,
)
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
        role_id=model.role_id,
        account_type=AccountType(model.account_type),
        role=role,
    )
