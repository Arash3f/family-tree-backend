import logging

from app.presentation.utils.error_codes import ERROR_MESSAGES


def resolve_message(code, lang: str) -> str:
    """
    Resolve a localized error message based on an error code and language.

    This function retrieves the appropriate error message from the
    ERROR_MESSAGES dictionary using the provided language and error code.

    If the requested language is not supported, the function falls back
    to English ("en"). If the error code does not exist in the language
    dictionary, a default message "Unknown error" is returned.

    Args:
        code: The error code identifier (usually an ErrorCode enum).
        lang (str): The requested language code (e.g., "fa", "en").

    Returns:
        str: The resolved localized error message.

    Example:
        >>> resolve_message(ErrorCode.MARRIAGE_NOT_FOUND, "fa")
        "ازدواج مورد نظر یافت نشد"
    """

    # Fallback to English if the language is not supported
    if lang not in ERROR_MESSAGES:
        lang = "en"

    msg = ERROR_MESSAGES[lang].get(code)

    if msg:
        return msg

    # Log missing translation
    logger = logging.getLogger(__name__)
    logger.warning(f"Missing translation for code '{code}' in language '{lang}'")

    # Final fallback
    return "Unknown error"
