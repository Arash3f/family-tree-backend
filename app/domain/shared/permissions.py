from collections.abc import Iterable


class Permissions:
    USER_CREATE = "user_create"
    USER_DELETE = "user_delete"
    USER_READ = "user_read"
    USER_UPDATE = "user_update"

    ROLE_CREATE = "role_create"
    ROLE_DELETE = "role_delete"
    ROLE_READ = "role_read"
    ROLE_UPDATE = "role_update"

    PERMISSION_READ = "permission_read"

    MARRIAGE_CREATE = "marriage_create"
    MARRIAGE_READ = "marriage_read"
    MARRIAGE_UPDATE = "marriage_update"
    MARRIAGE_DELETE = "marriage_delete"
    MARRIAGE_DIVORCE = "marriage_divorce"

    PERSON_CREATE = "person_create"
    PERSON_READ = "person_read"
    PERSON_UPDATE = "person_update"
    PERSON_DELETE = "person_delete"

    MEDIA_UPLOAD = "media_upload"

    TICKET_CREATE = "ticket_create"
    TICKET_READ = "ticket_read"
    TICKET_REPLY = "ticket_reply"

    TREE_CREATE = "tree_create"
    TREE_READ = "tree_read"
    TREE_UPDATE = "tree_update"
    TREE_DELETE = "tree_delete"
    TREE_MEMBER_ADD = "tree_member_add"
    TREE_MEMBER_REMOVE = "tree_member_remove"

    # Selecting a permission also requires these (UI-coupled capabilities).
    PERMISSION_REQUIREMENTS: dict[str, tuple[str, ...]] = {
        USER_CREATE: (USER_READ, ROLE_READ),
        USER_UPDATE: (USER_READ, ROLE_READ),
        USER_DELETE: (USER_READ,),
        ROLE_CREATE: (ROLE_READ, PERMISSION_READ),
        ROLE_UPDATE: (ROLE_READ, PERMISSION_READ),
        ROLE_DELETE: (ROLE_READ,),
        PERSON_READ: (TREE_READ,),
        PERSON_CREATE: (PERSON_READ,),
        PERSON_UPDATE: (PERSON_READ,),
        PERSON_DELETE: (PERSON_READ,),
        MARRIAGE_READ: (TREE_READ, PERSON_READ),
        MARRIAGE_CREATE: (MARRIAGE_READ,),
        MARRIAGE_UPDATE: (MARRIAGE_READ,),
        MARRIAGE_DELETE: (MARRIAGE_READ,),
        MARRIAGE_DIVORCE: (MARRIAGE_READ,),
        MEDIA_UPLOAD: (PERSON_READ, TREE_READ),
        TICKET_CREATE: (TICKET_READ,),
        TICKET_REPLY: (TICKET_READ,),
        TREE_CREATE: (TREE_READ,),
        TREE_UPDATE: (TREE_READ,),
        TREE_DELETE: (TREE_READ,),
        TREE_MEMBER_ADD: (TREE_READ, USER_READ),
        TREE_MEMBER_REMOVE: (TREE_READ,),
    }

    # (description_en, description_fa)
    PERMISSION_DESCRIPTIONS: dict[str, tuple[str, str]] = {
        USER_CREATE: (
            "Create new user accounts and assign an initial role.",
            "ایجاد حساب کاربری جدید و اختصاص نقش اولیه.",
        ),
        USER_DELETE: (
            "Permanently remove user accounts from the system.",
            "حذف دائمی حساب‌های کاربری از سامانه.",
        ),
        USER_READ: (
            "View the list of users and their basic profile details.",
            "مشاهده فهرست کاربران و جزئیات پایه پروفایل آن‌ها.",
        ),
        USER_UPDATE: (
            "Edit user accounts, including assigned roles.",
            "ویرایش حساب‌های کاربری، از جمله نقش اختصاص‌داده‌شده.",
        ),
        ROLE_CREATE: (
            "Create new roles and choose which permissions they include.",
            "ایجاد نقش جدید و انتخاب دسترسی‌های آن.",
        ),
        ROLE_DELETE: (
            "Delete roles that are no longer needed.",
            "حذف نقش‌هایی که دیگر لازم نیستند.",
        ),
        ROLE_READ: (
            "View available roles and their permission sets.",
            "مشاهده نقش‌های موجود و مجموعه دسترسی‌های آن‌ها.",
        ),
        ROLE_UPDATE: (
            "Change a role's name or the permissions it grants.",
            "تغییر نام نقش یا دسترسی‌هایی که اعطا می‌کند.",
        ),
        PERMISSION_READ: (
            "View the catalog of permissions that can be assigned to roles.",
            "مشاهده فهرست دسترسی‌هایی که می‌توان به نقش‌ها اختصاص داد.",
        ),
        MARRIAGE_CREATE: (
            "Record a new marriage between two people in a family tree.",
            "ثبت ازدواج جدید بین دو نفر در شجره‌نامه.",
        ),
        MARRIAGE_READ: (
            "View marriage records linked to people in a family tree.",
            "مشاهده سوابق ازدواج مرتبط با افراد در شجره‌نامه.",
        ),
        MARRIAGE_UPDATE: (
            "Edit existing marriage details such as spouses or dates.",
            "ویرایش جزئیات ازدواج موجود مانند همسران یا تاریخ‌ها.",
        ),
        MARRIAGE_DELETE: (
            "Remove a marriage record from a family tree.",
            "حذف سابقه ازدواج از شجره‌نامه.",
        ),
        MARRIAGE_DIVORCE: (
            "Mark a marriage as divorced and set the divorce date.",
            "ثبت طلاق برای یک ازدواج و تعیین تاریخ آن.",
        ),
        PERSON_CREATE: (
            "Add a new person to a family tree.",
            "افزودن فرد جدید به شجره‌نامه.",
        ),
        PERSON_READ: (
            "View people and their details within accessible family trees.",
            "مشاهده افراد و جزئیات آن‌ها در شجره‌نامه‌های قابل دسترس.",
        ),
        PERSON_UPDATE: (
            "Edit a person's biographical and relationship details.",
            "ویرایش اطلاعات زندگی‌نامه‌ای و روابط یک فرد.",
        ),
        PERSON_DELETE: (
            "Remove a person from a family tree.",
            "حذف یک فرد از شجره‌نامه.",
        ),
        MEDIA_UPLOAD: (
            "Upload photos and other media attached to people.",
            "آپلود عکس و سایر رسانه‌های متصل به افراد.",
        ),
        TICKET_CREATE: (
            "Open a new support ticket and reply on tickets you created.",
            "ایجاد تیکت پشتیبانی جدید و پاسخ روی تیکت‌های خودتان.",
        ),
        TICKET_READ: (
            "View your own support tickets.",
            "مشاهده تیکت‌های پشتیبانی خودتان.",
        ),
        TICKET_REPLY: (
            "Reply to any ticket, see the full queue, and change status.",
            "پاسخ به هر تیکت، مشاهده کل صف و تغییر وضعیت.",
        ),
        TREE_CREATE: (
            "Create a new family tree.",
            "ایجاد شجره‌نامه جدید.",
        ),
        TREE_READ: (
            "Open and browse family trees you belong to.",
            "باز کردن و مرور شجره‌نامه‌هایی که عضو آن‌ها هستید.",
        ),
        TREE_UPDATE: (
            "Rename or update settings of a family tree.",
            "تغییر نام یا تنظیمات یک شجره‌نامه.",
        ),
        TREE_DELETE: (
            "Permanently delete a family tree.",
            "حذف دائمی یک شجره‌نامه.",
        ),
        TREE_MEMBER_ADD: (
            "Invite or add other users as members of a family tree.",
            "دعوت یا افزودن کاربران دیگر به‌عنوان عضو شجره‌نامه.",
        ),
        TREE_MEMBER_REMOVE: (
            "Remove members from a family tree.",
            "حذف اعضا از یک شجره‌نامه.",
        ),
    }

    @classmethod
    def get_all_permissions(cls) -> list[str]:
        return [
            value
            for name, value in vars(cls).items()
            if not name.startswith("_") and isinstance(value, str)
        ]

    @classmethod
    def get_count(cls) -> int:
        return len(cls.get_all_permissions())

    @classmethod
    def get_direct_requirements(cls, permission_name: str) -> tuple[str, ...]:
        return cls.PERMISSION_REQUIREMENTS.get(permission_name, ())

    @classmethod
    def expand_with_requirements(cls, permission_names: Iterable[str]) -> set[str]:
        """Return permission names plus all transitive required companions."""
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
    def get_descriptions(cls, permission_name: str) -> tuple[str, str]:
        """Return (description_en, description_fa) for a permission name."""
        return cls.PERMISSION_DESCRIPTIONS.get(permission_name, ("", ""))
