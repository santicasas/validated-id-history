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
# (URLs, hashtags, mencions, caràcters de control Unicode)
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

# Seqüències de 3+ paraules en Title Case (noms propis: persones, institucions,
# llocs) que poden enganyar el detector quan el text és en un altre idioma.
# Exemples: "Ajuntament de Terrassa", "Generalitat de Catalunya", "Open Government of Catalonia"
# S'eliminen les cadenes de ≥3 paraules on cada paraula comença per majúscula,
# permetent connectors minúsculs entre elles (de, del, of, the, van, i, etc.)
_CONNECTOR = r'(?:de|del|dels|d\'|la|les|el|els|i|of|the|and|for|van|von|der|di|le|du|des|al|als|da|do|dos|das|a|en|y|e|mit|und|et|ou)\s+'
_CAP_WORD   = r'[A-ZÁÉÍÓÚÀÈÌÒÙÄÖÜÑÇ\u00C0-\u024F][a-záéíóúàèìòùäöüñç\u00C0-\u024F\w]*'
_PROPER_RE  = re.compile(
    r'(?:' + _CAP_WORD + r'\s+(?:' + _CONNECTOR + r')?)' + r'{2,}' + _CAP_WORD,
    re.UNICODE
)


def _clean_for_detection(text: str) -> str:
    """Elimina elements idiomàticament neutres del text per millorar la detecció.

    - URLs, hashtags, mencions, caràcters de control Unicode
    - Seqüències de ≥3 paraules en Title Case (noms propis de persones/llocs/entitats)
    """
    cleaned = _STRIP_RE.sub(' ', text)
    # Strip proper noun chains (3+ consecutive capitalized words / with connectors)
    cleaned = _PROPER_RE.sub(' ', cleaned)
    # Comprimeix espais múltiples i línies en blanc
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = re.sub(r'\n{2,}', '\n', cleaned)
    return cleaned.strip()


def detect_lang(text: str) -> str:
    """
    Retorna el codi d'idioma de 2 lletres (ES, EN, DE, FR, CA, PT)
    o '' si el text és massa curt o la confiança és baixa.

    Primer neteja el text (URLs, hashtags, mencions, caràcters de control,
    noms propis) per reduir falsos positius entre llengües similars.
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
