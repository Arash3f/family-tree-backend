from enum import Enum


class ErrorCode(int, Enum):
    UN_EXPECTED_ID = 1
    INVALID_PAGE_SIZE = 2
    INVALID_PAGE = 3
    # -----------------------
    # |     Domain Auth     |
    # -----------------------
    InvalidCredentials = 900
    SESSION_NOT_FOUND = 901
    # -----------------------
    # |    Domain Person    |
    # -----------------------
    SELF_PARENT = 1100
    INVALID_BIRTH_DAY = 1101
    HUSBAND_NOT_FOUND = 1102
    WIFE_NOT_FOUND = 1103
    PERSON_NOT_FOUND = 1104
    SAME_PARENT = 1105
    INVALID_GENDER = 1106
    PERSON_HAS_MARRIAGES = 1107
    INVALID_MEDIA_CONTENT_TYPE = 1108
    MEDIA_TOO_LARGE = 1109
    INVALID_MEDIA_OBJECT_KEY = 1110
    MEDIA_OBJECT_NOT_FOUND = 1111
    TOO_MANY_BIOLOGICAL_PARENTS = 1112
    INVALID_PARENT_MARRIAGE = 1113
    PERSON_HAS_CHILDREN = 1114
    # -----------------------
    # |    Domain Marriage    |
    # -----------------------
    SELF_MARRIAGE = 1200
    DIVORCED_BEFORE_MARRIAGE = 1201
    MARRIAGE_AFTER_DIVORCE = 1202
    UNDERAGE_MARRIAGE = 1203
    INVALID_MARRIAGE_GENDER = 1204
    MARRIAGE_NOT_FOUND = 1205
    ACTIVE_MARRIAGE_EXISTS = 1206
    MARRIAGE_ALREADY_DIVORCED = 1207
    # -----------------------
    # |  Permission Person  |
    # -----------------------
    PERMISSION_NOT_FOUND = 1300
    PERMISSION_DENIED = 1301
    # -----------------------
    # |     User Person     |
    # -----------------------
    USER_NOT_FOUND = 1400
    USER_PASSWORD_INCORECT = 1401
    PASSWORD_CONFIRMATION_MISMATCH = 1402
    SELF_ROLE_CHANGE = 1403
    PRIVILEGED_USER_MODIFICATION = 1404
    USERNAME_ALREADY_EXISTS = 1405
    EMAIL_ALREADY_EXISTS = 1406
    ACCOUNT_DEACTIVATED = 1407
    PHONE_ALREADY_EXISTS = 1408
    # -----------------------
    # |     Role Person     |
    # -----------------------
    ROLE_NOT_FOUND = 1500
    ROLE_NAME_DUPLICATED = 1501
    ROLE_PROTECTED = 1502
    # -----------------------
    # |    Domain Ticket    |
    # -----------------------
    TICKET_NOT_FOUND = 1600
    TICKET_CLOSED = 1601
    TICKET_ACCESS_DENIED = 1602
    # -----------------------
    # |  Domain FamilyTree  |
    # -----------------------
    FAMILY_TREE_NOT_FOUND = 1700
    TREE_MEMBERSHIP_DENIED = 1701
    TREE_OWNER_REQUIRED = 1702
    TREE_MEMBER_ALREADY_EXISTS = 1703
    TREE_MEMBER_NOT_FOUND = 1704
    CANNOT_REMOVE_LAST_OWNER = 1705
    PERSON_TREE_MISMATCH = 1706
    MARRIAGE_TREE_MISMATCH = 1707
    TREE_EXCEL_INVALID = 1708
    TREE_EXCEL_EMPTY = 1709
    TREE_ACCESS_DENIED = 1710
    FREE_ACCOUNT_LIMIT = 1711


ERROR_MESSAGES = {
    "en": {
        ErrorCode.UN_EXPECTED_ID: "Unexpected ID provided",
        ErrorCode.INVALID_PAGE_SIZE: "Invalid page size",
        ErrorCode.INVALID_PAGE: "Invalid page",
        # Domain Auth
        ErrorCode.InvalidCredentials: "Invalid credentials",
        ErrorCode.SESSION_NOT_FOUND: "Session not found",
        # Domain Person
        ErrorCode.SELF_PARENT: "A person cannot be their own parent",
        ErrorCode.INVALID_BIRTH_DAY: "Invalid birth date",
        ErrorCode.HUSBAND_NOT_FOUND: "Husband not found",
        ErrorCode.WIFE_NOT_FOUND: "Wife not found",
        ErrorCode.PERSON_NOT_FOUND: "Person not found",
        ErrorCode.SAME_PARENT: "Person cannot have the same parent more than once",
        ErrorCode.INVALID_GENDER: "Person's gender is invalid",
        ErrorCode.PERSON_HAS_MARRIAGES: (
            "Person cannot be deleted while linked to marriages"
        ),
        ErrorCode.INVALID_MEDIA_CONTENT_TYPE: "Unsupported media content type",
        ErrorCode.MEDIA_TOO_LARGE: "Uploaded media exceeds size limit",
        ErrorCode.INVALID_MEDIA_OBJECT_KEY: "Invalid media object key",
        ErrorCode.MEDIA_OBJECT_NOT_FOUND: "Media object not found",
        ErrorCode.TOO_MANY_BIOLOGICAL_PARENTS: (
            "Child cannot have more than two biological parents"
        ),
        ErrorCode.INVALID_PARENT_MARRIAGE: (
            "Biological parents must match the origin marriage spouses"
        ),
        ErrorCode.PERSON_HAS_CHILDREN: (
            "Person cannot be deleted while linked to children"
        ),
        # Domain Marriage
        ErrorCode.SELF_MARRIAGE: "A person cannot marry themselves",
        ErrorCode.DIVORCED_BEFORE_MARRIAGE: (
            "A divorced person cannot be married again without proper validation"
        ),
        ErrorCode.MARRIAGE_AFTER_DIVORCE: (
            "Marriage cannot be registered for a divorced person"
        ),
        ErrorCode.UNDERAGE_MARRIAGE: "Marriage is not allowed for underage persons",
        ErrorCode.INVALID_MARRIAGE_GENDER: (
            "Marriage is only allowed between a male and a female"
        ),
        ErrorCode.MARRIAGE_NOT_FOUND: "Marriage not found",
        ErrorCode.ACTIVE_MARRIAGE_EXISTS: "Person already has an active marriage",
        ErrorCode.MARRIAGE_ALREADY_DIVORCED: "Marriage is already divorced",
        # Domain Permission
        ErrorCode.PERMISSION_NOT_FOUND: "Permission not found",
        ErrorCode.PERMISSION_DENIED: "Permission denied",
        # Domain User
        ErrorCode.USER_NOT_FOUND: "User not found",
        ErrorCode.USER_PASSWORD_INCORECT: "User password incorrect",
        ErrorCode.PASSWORD_CONFIRMATION_MISMATCH: (
            "Password and its confirmation do not match"
        ),
        ErrorCode.SELF_ROLE_CHANGE: "You cannot change your own role",
        ErrorCode.PRIVILEGED_USER_MODIFICATION: (
            "Only an administrator can grant or modify the administrator role"
        ),
        ErrorCode.USERNAME_ALREADY_EXISTS: "Username is already taken",
        ErrorCode.EMAIL_ALREADY_EXISTS: "Email is already registered",
        ErrorCode.PHONE_ALREADY_EXISTS: "Phone number is already registered",
        ErrorCode.ACCOUNT_DEACTIVATED: (
            "Your account has been deactivated. Please contact support."
        ),
        # Domain Role
        ErrorCode.ROLE_NOT_FOUND: "Role not found",
        ErrorCode.ROLE_NAME_DUPLICATED: "Role name duplicated",
        ErrorCode.ROLE_PROTECTED: "This role cannot be deleted",
        # Domain Ticket
        ErrorCode.TICKET_NOT_FOUND: "Ticket not found",
        ErrorCode.TICKET_CLOSED: "Ticket is closed",
        ErrorCode.TICKET_ACCESS_DENIED: "Ticket access denied",
        # Domain FamilyTree
        ErrorCode.FAMILY_TREE_NOT_FOUND: "Family tree not found",
        ErrorCode.TREE_MEMBERSHIP_DENIED: "You are not a member of this family tree",
        ErrorCode.TREE_OWNER_REQUIRED: "Only the tree owner can perform this action",
        ErrorCode.TREE_MEMBER_ALREADY_EXISTS: "User is already a member of this tree",
        ErrorCode.TREE_MEMBER_NOT_FOUND: "Tree membership not found",
        ErrorCode.CANNOT_REMOVE_LAST_OWNER: (
            "Cannot remove the last owner of a family tree"
        ),
        ErrorCode.PERSON_TREE_MISMATCH: "Person does not belong to this family tree",
        ErrorCode.MARRIAGE_TREE_MISMATCH: (
            "Marriage or related persons are not in this family tree"
        ),
        ErrorCode.TREE_EXCEL_INVALID: (
            "Excel file is invalid or does not match the expected template"
        ),
        ErrorCode.TREE_EXCEL_EMPTY: "Excel file has no people or marriages to import",
        ErrorCode.TREE_ACCESS_DENIED: "You do not have this access on the family tree",
        ErrorCode.FREE_ACCOUNT_LIMIT: "You are on a free account",
    },
    "fa": {
        ErrorCode.UN_EXPECTED_ID: "شناسهٔ ارسال‌شده نامعتبر است.",
        ErrorCode.INVALID_PAGE_SIZE: "تعداد موارد در هر صفحه نامعتبر است.",
        ErrorCode.INVALID_PAGE: "شمارهٔ صفحه نامعتبر است.",
        # Domain Auth
        ErrorCode.InvalidCredentials: "نام کاربری یا رمز عبور اشتباه است.",
        ErrorCode.SESSION_NOT_FOUND: "نشست پیدا نشد. لطفاً دوباره وارد شوید.",
        # Domain Person
        ErrorCode.SELF_PARENT: "هیچ فردی نمی‌تواند والد خودش باشد.",
        ErrorCode.INVALID_BIRTH_DAY: "تاریخ تولد معتبر نیست.",
        ErrorCode.HUSBAND_NOT_FOUND: "همسر مرد پیدا نشد.",
        ErrorCode.WIFE_NOT_FOUND: "همسر زن پیدا نشد.",
        ErrorCode.PERSON_NOT_FOUND: "فرد مورد نظر پیدا نشد.",
        ErrorCode.SAME_PARENT: "یک والد را نمی‌توان بیش از یک بار برای یک فرد ثبت کرد.",
        ErrorCode.INVALID_GENDER: "جنسیت واردشده معتبر نیست.",
        ErrorCode.PERSON_HAS_MARRIAGES: (
            "تا وقتی ازدواجی برای این فرد ثبت شده است، نمی‌توان او را حذف کرد."
        ),
        ErrorCode.INVALID_MEDIA_CONTENT_TYPE: "نوع این فایل پشتیبانی نمی‌شود.",
        ErrorCode.MEDIA_TOO_LARGE: "حجم فایل بیشتر از حد مجاز است.",
        ErrorCode.INVALID_MEDIA_OBJECT_KEY: "شناسهٔ فایل معتبر نیست.",
        ErrorCode.MEDIA_OBJECT_NOT_FOUND: "فایل مورد نظر پیدا نشد.",
        ErrorCode.TOO_MANY_BIOLOGICAL_PARENTS: (
            "هر فرزند حداکثر می‌تواند دو والد تنی داشته باشد."
        ),
        ErrorCode.INVALID_PARENT_MARRIAGE: (
            "والدین تنی باید همان دو همسرِ ازدواجی باشند که فرزند از آن به دنیا "
            "آمده است."
        ),
        ErrorCode.PERSON_HAS_CHILDREN: (
            "تا وقتی فرزندی برای این فرد ثبت شده است، نمی‌توان او را حذف کرد."
        ),
        # Domain Marriage
        ErrorCode.SELF_MARRIAGE: "هیچ فردی نمی‌تواند با خودش ازدواج کند.",
        ErrorCode.DIVORCED_BEFORE_MARRIAGE: (
            "ثبت ازدواج دوباره برای فرد طلاق‌گرفته بدون بررسی‌های لازم امکان‌پذیر نیست."
        ),
        ErrorCode.MARRIAGE_AFTER_DIVORCE: (
            "برای فرد طلاق‌گرفته نمی‌توان این ازدواج را ثبت کرد."
        ),
        ErrorCode.UNDERAGE_MARRIAGE: "ثبت ازدواج برای افراد زیر سن قانونی مجاز نیست.",
        ErrorCode.INVALID_MARRIAGE_GENDER: (
            "ازدواج فقط میان یک مرد و یک زن قابل ثبت است."
        ),
        ErrorCode.MARRIAGE_NOT_FOUND: "ازدواج مورد نظر پیدا نشد.",
        ErrorCode.ACTIVE_MARRIAGE_EXISTS: "این فرد در حال حاضر یک ازدواج فعال دارد.",
        ErrorCode.MARRIAGE_ALREADY_DIVORCED: "طلاق این ازدواج قبلاً ثبت شده است.",
        # Domain Permission
        ErrorCode.PERMISSION_NOT_FOUND: "دسترسی مورد نظر پیدا نشد.",
        ErrorCode.PERMISSION_DENIED: "شما اجازهٔ انجام این کار را ندارید.",
        # Domain User
        ErrorCode.USER_NOT_FOUND: "کاربر مورد نظر پیدا نشد.",
        ErrorCode.USER_PASSWORD_INCORECT: "رمز عبور اشتباه است.",
        ErrorCode.PASSWORD_CONFIRMATION_MISMATCH: "رمز عبور و تکرار آن یکسان نیستند.",
        ErrorCode.SELF_ROLE_CHANGE: "شما نمی‌توانید نقش خودتان را تغییر دهید.",
        ErrorCode.PRIVILEGED_USER_MODIFICATION: (
            "فقط مدیر سیستم می‌تواند نقش مدیر را به کسی بدهد یا آن را تغییر دهد."
        ),
        ErrorCode.USERNAME_ALREADY_EXISTS: (
            "این نام کاربری قبلاً ثبت شده است. نام دیگری انتخاب کنید."
        ),
        ErrorCode.EMAIL_ALREADY_EXISTS: "این ایمیل قبلاً ثبت شده است.",
        ErrorCode.PHONE_ALREADY_EXISTS: "این شمارهٔ موبایل قبلاً ثبت شده است.",
        ErrorCode.ACCOUNT_DEACTIVATED: (
            "حساب کاربری شما غیرفعال شده است. لطفاً با پشتیبانی تماس بگیرید."
        ),
        # Domain Role
        ErrorCode.ROLE_NOT_FOUND: "نقش مورد نظر پیدا نشد.",
        ErrorCode.ROLE_NAME_DUPLICATED: "نقشی با این نام از قبل وجود دارد.",
        ErrorCode.ROLE_PROTECTED: "این نقش قابل حذف نیست.",
        # Domain Ticket
        ErrorCode.TICKET_NOT_FOUND: "تیکت مورد نظر پیدا نشد.",
        ErrorCode.TICKET_CLOSED: "این تیکت بسته شده است.",
        ErrorCode.TICKET_ACCESS_DENIED: "شما به این تیکت دسترسی ندارید.",
        # Domain FamilyTree
        ErrorCode.FAMILY_TREE_NOT_FOUND: "شجره‌نامهٔ مورد نظر پیدا نشد.",
        ErrorCode.TREE_MEMBERSHIP_DENIED: "شما عضو این شجره‌نامه نیستید.",
        ErrorCode.TREE_OWNER_REQUIRED: (
            "فقط مالک شجره‌نامه می‌تواند این کار را انجام دهد."
        ),
        ErrorCode.TREE_MEMBER_ALREADY_EXISTS: "این کاربر از قبل عضو این شجره‌نامه است.",
        ErrorCode.TREE_MEMBER_NOT_FOUND: "عضو مورد نظر در این شجره‌نامه پیدا نشد.",
        ErrorCode.CANNOT_REMOVE_LAST_OWNER: "آخرین مالک شجره‌نامه را نمی‌توان حذف کرد.",
        ErrorCode.PERSON_TREE_MISMATCH: "این فرد متعلق به این شجره‌نامه نیست.",
        ErrorCode.MARRIAGE_TREE_MISMATCH: (
            "این ازدواج یا افراد مربوط به آن در این شجره‌نامه نیستند."
        ),
        ErrorCode.TREE_EXCEL_INVALID: (
            "فایل اکسل معتبر نیست یا با قالب فایل نمونه مطابقت ندارد."
        ),
        ErrorCode.TREE_EXCEL_EMPTY: (
            "در فایل اکسل هیچ فرد یا ازدواجی برای وارد کردن پیدا نشد."
        ),
        ErrorCode.TREE_ACCESS_DENIED: "شما این دسترسی را در این شجره‌نامه ندارید.",
        ErrorCode.FREE_ACCOUNT_LIMIT: (
            "حساب شما رایگان است و این امکان برای آن فعال نیست."
        ),
    },
}
