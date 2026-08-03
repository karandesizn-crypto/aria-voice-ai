from __future__ import annotations

from voice_agent.languages import resolve_language, supported_language_codes


def test_resolve_language_defaults_to_english() -> None:
    assert resolve_language(None).code == "en"
    assert resolve_language("").code == "en"
    assert resolve_language("unknown").code == "en"


def test_resolve_language_accepts_bcp47_prefix() -> None:
    locale = resolve_language("hi-IN")
    assert locale.code == "hi"
    assert locale.edge_voice.startswith("hi-")
    assert locale.stt_code == "hi"


def test_supported_languages_cover_core_locales() -> None:
    codes = supported_language_codes()
    for code in ("en", "hi", "es", "ta", "zh"):
        assert code in codes
