"""
lang_detect.py
Mòdul compartit per detectar l'idioma d'un text amb lingua-language-detector.
"""
import re
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
# 0.35: diferència mínima entre la 1a i 2a llengua detectada.
_MIN_CONFIDENCE = 0.35

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

# Longitud mínima de text útil (després de neteja) per intentar la detecció
MIN_TEXT_LEN = 40

# Patrons que eliminem perquè no aporten informació lingüística
# (URLs, hashtags, mencions, emojis de bandera, caràcters de control Unicode)
_STRIP_RE = re.compile(
    r'https?://\S+'           # URLs
    r'|www\.\S+'              # URLs sense protocol
    r'|#\w+'                  # hashtags
    r'|@\S+'                  # mencions (@user, @[id])
    r'|[\u200b-\u200f'        # caràcters de control Unicode (zero-width, etc.)
    r'\u202a-\u202e'          # directional formatting characters
    r'\u2066-\u2069]'         # isolate directional marks
    , re.UNICODE
)


def _clean_for_detection(text: str) -> str:
    """Elimina elements idiomàticament neutres del text per millorar la detecció."""
    cleaned = _STRIP_RE.sub(' ', text)
    # Comprimeix espais múltiples i línies en blanc
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = re.sub(r'\n{2,}', '\n', cleaned)
    return cleaned.strip()


def detect_lang(text: str) -> str:
    """
    Retorna el codi d'idioma de 2 lletres (ES, EN, DE, FR, CA, PT)
    o '' si el text és massa curt o la confiança és baixa.

    Primer neteja el text (URLs, hashtags, mencions, caràcters de control)
    per reduir falsos positius entre llengües similars (ES/PT, ES/CA, EN/DE).
    """
    if not text:
        return ''
    cleaned = _clean_for_detection(text)
    if len(cleaned) < MIN_TEXT_LEN:
        return ''
    result = _detector.detect_language_of(cleaned)
    if result is None:
        return ''
    return _CODE_MAP.get(result, '')
