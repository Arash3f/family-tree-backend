from enum import Enum


class ErrorCode(int, Enum):
    UN_EXPECTED_ID = 1
    INVALID_PAGE_SIZE = 2
    INVALID_PAGE = 3
    # -----------------------
    # |     Domain Auth     |
    # -----------------------
    InvalidCredentials = 900
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
    # -----------------------
    # |    Domain Person    |
    # -----------------------
    SELF_MARRIAGE = 1200
    DIVORCED_BEFORE_MARRIAGE = 1201
    MARRIAGE_AFTER_DIVORCE = 1202
    UNDERAGE_MARRIAGE = 1203
    INVALID_MARRIAGE_GENDER = 1204
    MARRIAGE_NOT_FOUND = 1205
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
    # -----------------------
    # |     Role Person     |
    # -----------------------
    ROLE_NOT_FOUND = 1500


ERROR_MESSAGES = {
    "en": {
        ErrorCode.UN_EXPECTED_ID: "Unexpected ID provided",
        ErrorCode.INVALID_PAGE_SIZE: "Invalid page size",
        ErrorCode.INVALID_PAGE: "Invalid page",
        # Domain Auth
        ErrorCode.InvalidCredentials: "Invalid credentials",
        # Domain Person
        ErrorCode.SELF_PARENT: "A person cannot be their own parent",
        ErrorCode.INVALID_BIRTH_DAY: "Invalid birth date",
        ErrorCode.HUSBAND_NOT_FOUND: "Husband not found",
        ErrorCode.WIFE_NOT_FOUND: "Wife not found",
        ErrorCode.PERSON_NOT_FOUND: "Person not found",
        ErrorCode.SAME_PARENT: "Person's father & mother can not be the same",
        ErrorCode.INVALID_GENDER: "Person's gender is invalid",
        # Domain Marriage
        ErrorCode.SELF_MARRIAGE: "A person cannot marry themselves",
        ErrorCode.DIVORCED_BEFORE_MARRIAGE: "A divorced person cannot be married again without proper validation",
        ErrorCode.MARRIAGE_AFTER_DIVORCE: "Marriage cannot be registered for a divorced person",
        ErrorCode.UNDERAGE_MARRIAGE: "Marriage is not allowed for underage persons",
        ErrorCode.INVALID_MARRIAGE_GENDER: "Marriage is only allowed between a male and a female",
        ErrorCode.MARRIAGE_NOT_FOUND: "Marriage not found",
        # Domain Permission
        ErrorCode.PERMISSION_NOT_FOUND: "Permission not found",
        ErrorCode.PERMISSION_DENIED: "Permission denied",
        # Domain User
        ErrorCode.USER_NOT_FOUND: "User not found",
        ErrorCode.USER_PASSWORD_INCORECT: "User password incorect",
        # Domain Role
        ErrorCode.ROLE_NOT_FOUND: "Role not found",
    },
    "fa": {
        ErrorCode.UN_EXPECTED_ID: "شناسه غیرمنتظره",
        ErrorCode.INVALID_PAGE_SIZE: "اندازه صفحه نامعتبر است",
        ErrorCode.INVALID_PAGE: "شماره صفحه اشتباه است",
        # Domain Auth
        ErrorCode.InvalidCredentials: "Invalid credentials",
        # Domain Person
        ErrorCode.SELF_PARENT: "یک شخص نمی‌تواند والد خودش باشد",
        ErrorCode.INVALID_BIRTH_DAY: "تاریخ تولد نامعتبر است",
        ErrorCode.HUSBAND_NOT_FOUND: "شوهر یافت نشد",
        ErrorCode.WIFE_NOT_FOUND: "همسر یافت نشد",
        ErrorCode.PERSON_NOT_FOUND: "شخص مورد نظر یافت نشد",
        ErrorCode.SAME_PARENT: "شخص نمیتواند پدر و مادر یکسان داشته باشد",
        ErrorCode.INVALID_GENDER: "جنسیت شخص نامعتبر است",
        # Domain Marriage
        ErrorCode.SELF_MARRIAGE: "یک شخص نمی‌تواند با خودش ازدواج کند",
        ErrorCode.DIVORCED_BEFORE_MARRIAGE: "فردی که طلاق گرفته است بدون اعتبارسنجی مناسب نمی‌تواند دوباره ازدواج کند",
        ErrorCode.MARRIAGE_AFTER_DIVORCE: "برای فرد مطلقه امکان ثبت این ازدواج وجود ندارد",
        ErrorCode.UNDERAGE_MARRIAGE: "ازدواج برای افراد زیر سن قانونی مجاز نیست",
        ErrorCode.INVALID_MARRIAGE_GENDER: "ازدواج فقط بین یک مرد و یک زن مجاز است",
        ErrorCode.MARRIAGE_NOT_FOUND: "ازدواج مورد نظر یافت نشد",
        # Domain Permission
        ErrorCode.PERMISSION_NOT_FOUND: "دسترسی پیدا نشد",
        ErrorCode.PERMISSION_DENIED: "عدم وجود دسترسی",
        # Domain User
        ErrorCode.USER_NOT_FOUND: "کاربر پیدا نشد",
        ErrorCode.USER_PASSWORD_INCORECT: "رمز کاربر اشتباه است",
        # Domain Role
        ErrorCode.ROLE_NOT_FOUND: "نقش پیدا نشد",
    },
}
