"""
lang_detect.py
Mòdul compartit per detectar l'idioma d'un text amb lingua-language-detector.
"""
from lingua import Language, LanguageDetectorBuilder

# Idiomes rellevants per a Validated ID
_LANGS = [
    Language.SPANISH,
    Language.ENGLISH,
    Language.GERMAN,
    Language.FRENCH,
    Language.CATALAN,
    Language.PORTUGUESE,
]

# Mínim de confiança relativa per acceptar el resultat
_MIN_CONFIDENCE = 0.15

_detector = LanguageDetectorBuilder.from_languages(*_LANGS) \
    .with_minimum_relative_distance(_MIN_CONFIDENCE) \
    .build()

# Mapeig de l'enum de lingua a codi ISO 639-1
_CODE_MAP = {
    Language.SPANISH:    'ES',
    Language.ENGLISH:    'EN',
    Language.GERMAN:     'DE',
    Language.FRENCH:     'FR',
    Language.CATALAN:    'CA',
    Language.PORTUGUESE: 'PT',
}

# Longitud mínima de text per intentar la detecció
MIN_TEXT_LEN = 30


def detect_lang(text: str) -> str:
    """
    Retorna el codi d'idioma de 2 lletres (ES, EN, DE, FR, CA, PT)
    o '' si el text és massa curt o la confiança és baixa.
    """
    if not text or len(text.strip()) < MIN_TEXT_LEN:
        return ''
    result = _detector.detect_language_of(text)
    if result is None:
        return ''
    return _CODE_MAP.get(result, '')
