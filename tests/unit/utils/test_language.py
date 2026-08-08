from types import SimpleNamespace

from app.presentation.rest.utils.language import detect_language


def test_detect_language_fa_variants():
    assert detect_language(SimpleNamespace(headers={"accept-language": "fa"})) == "fa"
    assert (
        detect_language(SimpleNamespace(headers={"accept-language": "fa-IR"})) == "fa"
    )
    assert (
        detect_language(SimpleNamespace(headers={"accept-language": "fa-IR,en;q=0.9"}))
        == "fa"
    )


def test_detect_language_en_default():
    assert detect_language(SimpleNamespace(headers={"accept-language": "en"})) == "en"
    assert detect_language(SimpleNamespace(headers={})) == "en"
