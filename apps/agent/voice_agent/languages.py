from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VoiceLanguage:
    """Locale used for STT + Edge TTS + reply language."""

    code: str
    label: str
    stt_code: str
    edge_voice: str
    greeting_instruction: str


# Curated Edge Neural voices — keep labels user-facing and codes API-stable.
SUPPORTED_LANGUAGES: tuple[VoiceLanguage, ...] = (
    VoiceLanguage(
        code="en",
        label="English",
        stt_code="en",
        edge_voice="en-US-JennyNeural",
        greeting_instruction="Greet the user briefly in English.",
    ),
    VoiceLanguage(
        code="hi",
        label="Hindi",
        stt_code="hi",
        edge_voice="hi-IN-SwaraNeural",
        greeting_instruction="Greet the user briefly in Hindi.",
    ),
    VoiceLanguage(
        code="es",
        label="Spanish",
        stt_code="es",
        edge_voice="es-ES-ElviraNeural",
        greeting_instruction="Greet the user briefly in Spanish.",
    ),
    VoiceLanguage(
        code="fr",
        label="French",
        stt_code="fr",
        edge_voice="fr-FR-DeniseNeural",
        greeting_instruction="Greet the user briefly in French.",
    ),
    VoiceLanguage(
        code="de",
        label="German",
        stt_code="de",
        edge_voice="de-DE-KatjaNeural",
        greeting_instruction="Greet the user briefly in German.",
    ),
    VoiceLanguage(
        code="pt",
        label="Portuguese",
        stt_code="pt",
        edge_voice="pt-BR-FranciscaNeural",
        greeting_instruction="Greet the user briefly in Portuguese.",
    ),
    VoiceLanguage(
        code="it",
        label="Italian",
        stt_code="it",
        edge_voice="it-IT-ElsaNeural",
        greeting_instruction="Greet the user briefly in Italian.",
    ),
    VoiceLanguage(
        code="ja",
        label="Japanese",
        stt_code="ja",
        edge_voice="ja-JP-NanamiNeural",
        greeting_instruction="Greet the user briefly in Japanese.",
    ),
    VoiceLanguage(
        code="ko",
        label="Korean",
        stt_code="ko",
        edge_voice="ko-KR-SunHiNeural",
        greeting_instruction="Greet the user briefly in Korean.",
    ),
    VoiceLanguage(
        code="zh",
        label="Chinese",
        stt_code="zh",
        edge_voice="zh-CN-XiaoxiaoNeural",
        greeting_instruction="Greet the user briefly in Mandarin Chinese.",
    ),
    VoiceLanguage(
        code="ar",
        label="Arabic",
        stt_code="ar",
        edge_voice="ar-SA-ZariyahNeural",
        greeting_instruction="Greet the user briefly in Arabic.",
    ),
    VoiceLanguage(
        code="ta",
        label="Tamil",
        stt_code="ta",
        edge_voice="ta-IN-PallaviNeural",
        greeting_instruction="Greet the user briefly in Tamil.",
    ),
    VoiceLanguage(
        code="te",
        label="Telugu",
        stt_code="te",
        edge_voice="te-IN-ShrutiNeural",
        greeting_instruction="Greet the user briefly in Telugu.",
    ),
    VoiceLanguage(
        code="mr",
        label="Marathi",
        stt_code="mr",
        edge_voice="mr-IN-AarohiNeural",
        greeting_instruction="Greet the user briefly in Marathi.",
    ),
    VoiceLanguage(
        code="bn",
        label="Bengali",
        stt_code="bn",
        edge_voice="bn-IN-TanishaaNeural",
        greeting_instruction="Greet the user briefly in Bengali.",
    ),
)

_BY_CODE = {lang.code: lang for lang in SUPPORTED_LANGUAGES}
DEFAULT_LANGUAGE_CODE = "en"


def resolve_language(code: str | None) -> VoiceLanguage:
    if not code:
        return _BY_CODE[DEFAULT_LANGUAGE_CODE]
    normalized = code.strip().lower().replace("_", "-")
    if normalized in _BY_CODE:
        return _BY_CODE[normalized]
    # Accept BCP-47 prefixes like en-US → en
    primary = normalized.split("-", 1)[0]
    return _BY_CODE.get(primary, _BY_CODE[DEFAULT_LANGUAGE_CODE])


def supported_language_codes() -> set[str]:
    return set(_BY_CODE)
