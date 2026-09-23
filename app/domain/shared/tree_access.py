from collections.abc import Iterable


class TreeAccessPermissions:
    """Per-tree membership capabilities (cascading like system RBAC)."""

    VIEW = "view"
    PERSON_CREATE = "person_create"
    PERSON_UPDATE = "person_update"
    PERSON_DELETE = "person_delete"
    MARRIAGE_CREATE = "marriage_create"
    MARRIAGE_UPDATE = "marriage_update"
    MARRIAGE_DELETE = "marriage_delete"
    MARRIAGE_DIVORCE = "marriage_divorce"
    UPLOAD_PHOTO = "upload_photo"
    MEMBER_ADD = "member_add"
    MEMBER_REMOVE = "member_remove"
    VIEW_BIRTH_DATE = "view_birth_date"
    VIEW_MARRIAGE_DATE = "view_marriage_date"
    VIEW_PHOTO = "view_photo"
    TICKET_MANAGE = "ticket_manage"

    ALL: tuple[str, ...] = (
        VIEW,
        PERSON_CREATE,
        PERSON_UPDATE,
        PERSON_DELETE,
        MARRIAGE_CREATE,
        MARRIAGE_UPDATE,
        MARRIAGE_DELETE,
        MARRIAGE_DIVORCE,
        UPLOAD_PHOTO,
        MEMBER_ADD,
        MEMBER_REMOVE,
        VIEW_BIRTH_DATE,
        VIEW_MARRIAGE_DATE,
        VIEW_PHOTO,
        TICKET_MANAGE,
    )

    # Selecting a capability also requires these.
    REQUIREMENTS: dict[str, tuple[str, ...]] = {
        PERSON_CREATE: (VIEW,),
        # Editing must expose protected values so a full form cannot silently
        # overwrite values the member was not allowed to see.
        PERSON_UPDATE: (VIEW, VIEW_BIRTH_DATE, VIEW_PHOTO),
        PERSON_DELETE: (VIEW,),
        MARRIAGE_CREATE: (VIEW,),
        MARRIAGE_UPDATE: (VIEW, VIEW_MARRIAGE_DATE),
        MARRIAGE_DELETE: (VIEW,),
        MARRIAGE_DIVORCE: (VIEW, VIEW_MARRIAGE_DATE),
        UPLOAD_PHOTO: (VIEW, VIEW_PHOTO),
        MEMBER_ADD: (VIEW,),
        MEMBER_REMOVE: (VIEW,),
        VIEW_BIRTH_DATE: (VIEW,),
        VIEW_MARRIAGE_DATE: (VIEW,),
        VIEW_PHOTO: (VIEW,),
        TICKET_MANAGE: (VIEW,),
    }

    LABELS_FA: dict[str, str] = {
        VIEW: "مشاهده",
        PERSON_CREATE: "افزودن فرد",
        PERSON_UPDATE: "ویرایش فرد",
        PERSON_DELETE: "حذف فرد",
        MARRIAGE_CREATE: "افزودن ازدواج",
        MARRIAGE_UPDATE: "ویرایش ازدواج",
        MARRIAGE_DELETE: "حذف ازدواج",
        MARRIAGE_DIVORCE: "ثبت طلاق",
        UPLOAD_PHOTO: "بارگذاری عکس",
        MEMBER_ADD: "افزودن یا ویرایش عضو",
        MEMBER_REMOVE: "حذف عضو",
        VIEW_BIRTH_DATE: "مشاهدهٔ تاریخ تولد",
        VIEW_MARRIAGE_DATE: "مشاهدهٔ تاریخ ازدواج",
        VIEW_PHOTO: "مشاهدهٔ عکس",
        TICKET_MANAGE: "مدیریت تیکت‌ها",
    }

    LABELS_EN: dict[str, str] = {
        VIEW: "View",
        PERSON_CREATE: "Create people",
        PERSON_UPDATE: "Update people",
        PERSON_DELETE: "Delete people",
        MARRIAGE_CREATE: "Create marriages",
        MARRIAGE_UPDATE: "Update marriages",
        MARRIAGE_DELETE: "Delete marriages",
        MARRIAGE_DIVORCE: "Record divorces",
        UPLOAD_PHOTO: "Upload photos",
        MEMBER_ADD: "Add or update members",
        MEMBER_REMOVE: "Remove members",
        VIEW_BIRTH_DATE: "View birth dates",
        VIEW_MARRIAGE_DATE: "View marriage dates",
        VIEW_PHOTO: "View photos",
        TICKET_MANAGE: "Manage tickets",
    }

    # Non-view capabilities that unlock the tree management / settings surface.
    MANAGEMENT: tuple[str, ...] = (
        PERSON_CREATE,
        PERSON_UPDATE,
        PERSON_DELETE,
        MARRIAGE_CREATE,
        MARRIAGE_UPDATE,
        MARRIAGE_DELETE,
        MARRIAGE_DIVORCE,
        UPLOAD_PHOTO,
        MEMBER_ADD,
        MEMBER_REMOVE,
        TICKET_MANAGE,
    )

    # The only capabilities the public demo tree ever grants. Read-only by
    # construction: every write capability is absent, so a demo visitor is
    # refused by the same permission check that refuses any other member.
    DEMO: tuple[str, ...] = (
        VIEW,
        VIEW_BIRTH_DATE,
        VIEW_MARRIAGE_DATE,
        VIEW_PHOTO,
    )

    @classmethod
    def grants_demo(cls, permission_name: str) -> bool:
        """Whether the public demo may satisfy this capability."""
        return permission_name in cls.DEMO

    @classmethod
    def get_all(cls) -> list[str]:
        return list(cls.ALL)

    @classmethod
    def is_known(cls, name: str) -> bool:
        return name in cls.ALL

    @classmethod
    def grants_management(cls, permission_names: Iterable[str]) -> bool:
        granted = set(permission_names)
        return bool(granted.intersection(cls.MANAGEMENT))

    @classmethod
    def get_direct_requirements(cls, permission_name: str) -> tuple[str, ...]:
        return cls.REQUIREMENTS.get(permission_name, ())

    @classmethod
    def expand_with_requirements(cls, permission_names: Iterable[str]) -> set[str]:
        result = set(permission_names)
        queue = list(result)
        while queue:
            current = queue.pop()
            for required in cls.get_direct_requirements(current):
                if required not in result:
                    result.add(required)
                    queue.append(required)
        return result

    @classmethod
    def normalize(cls, permission_names: Iterable[str]) -> list[str]:
        """Expand prerequisites and return a stable sorted list of known names."""
        known = {name for name in permission_names if cls.is_known(name)}
        if not known:
            known = {cls.VIEW}
        return sorted(cls.expand_with_requirements(known))
