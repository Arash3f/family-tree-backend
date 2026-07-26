import logging

from app.presentation.rest.errors.error_resolver import resolve_message
from app.utils.error_codes import ErrorCode


def test_resolve_message_en_and_fa():
    assert resolve_message(ErrorCode.PERSON_NOT_FOUND, "en") == "Person not found"
    assert resolve_message(ErrorCode.PERSON_NOT_FOUND, "fa") == "شخص مورد نظر یافت نشد"


def test_resolve_message_unsupported_lang_falls_back_to_en():
    assert resolve_message(ErrorCode.PERSON_NOT_FOUND, "de") == "Person not found"


def test_resolve_message_unknown_code(caplog):
    with caplog.at_level(logging.WARNING):
        assert resolve_message(999999, "en") == "Unknown error"
    assert "Missing translation" in caplog.text
