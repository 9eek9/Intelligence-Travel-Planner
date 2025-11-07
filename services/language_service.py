# services/language_service.py
from typing import Literal, Optional
from .gemini_service import chat_translate, chat_correct, chat_explain

# Normalization dictionary (short, long, country codes -> full language names)
LANGUAGE_MAP = {
    # --- Asian Languages ---
    "my": "burmese",
    "my-mm": "burmese",
    "mm": "burmese",
    "ms": "malay",
    "id": "indonesian",
    "ja": "japanese",
    "jp": "japanese",
    "ko": "korean",
    "th": "thai",
    "zh": "chinese",
    "zh-cn": "simplified chinese",
    "zh-sg": "simplified chinese",
    "zh-tw": "traditional chinese",
    "zh-hk": "traditional chinese",
    "vi": "vietnamese",
    "hi": "hindi",

    # --- European Languages ---
    "en": "english",
    "fr": "french",
    "de": "german",
    "es": "spanish",
    "it": "italian",
    "pt": "portuguese",
    "pt-br": "brazilian portuguese",
    "nl": "dutch",
    "sv": "swedish",
    "no": "norwegian",
    "da": "danish",
    "fi": "finnish",
    "pl": "polish",
    "ru": "russian",
    "uk": "ukrainian",
    "tr": "turkish",
    "el": "greek",
    "cs": "czech",
    "ro": "romanian",
    "hu": "hungarian",

    # --- Middle East / Africa ---
    "ar": "arabic",
    "fa": "persian",
    "ur": "urdu",
    "he": "hebrew",
    "sw": "swahili",
    "af": "afrikaans",

    # --- Others ---
    "la": "latin",
    "tl": "tagalog",
    "bn": "bengali",
    "ta": "tamil",
    "te": "telugu",
    "ml": "malayalam",
    "si": "sinhala",
    "km": "khmer",
    "ne": "nepali",
    "pa": "punjabi",
    "gu": "gujarati"
}

def normalize_lang(code: Optional[str]) -> Optional[str]:
    if not code:
        return None
    code = code.strip().lower()
    return LANGUAGE_MAP.get(code, code)

Mode = Literal["translate", "correct", "explain"]

def handle_language(text: str,
                    mode: Mode = "translate",
                    source_lang: Optional[str] = None,
                    target_lang: str = "en",
                    tone: str = "polite") -> str:
    # Normalize both
    source_lang = normalize_lang(source_lang)
    target_lang = normalize_lang(target_lang)

    if mode == "translate":
        return chat_translate(text=text, target_lang=target_lang, tone=tone)
    if mode == "correct":
        return chat_correct(text=text, lang=source_lang or "english")
    if mode == "explain":
        return chat_explain(text=text, lang=source_lang or "english")
    return chat_translate(text=text, target_lang=target_lang, tone=tone)

def list_supported_languages():
    """Return all supported language names as a sorted list."""
    return sorted(set(LANGUAGE_MAP.values()))