"""
lang_audit.py
Analitza la distribució de confiances de detecció d'idioma
per trobar el llindar òptim de _MIN_CONFIDENCE.

Mostra els casos ambigus (diferència petita entre 1a i 2a llengua).
"""

import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

from lingua import Language, LanguageDetectorBuilder

_LANGS = [
    Language.SPANISH,
    Language.ENGLISH,
    Language.GERMAN,
    Language.FRENCH,
    Language.CATALAN,
    Language.PORTUGUESE,
]

# Detector sense llindar per veure totes les confiances
_detector_raw = LanguageDetectorBuilder.from_languages(*_LANGS) \
    .with_minimum_relative_distance(0.0) \
    .build()

_CODE_MAP = {
    Language.SPANISH:    'ES',
    Language.ENGLISH:    'EN',
    Language.GERMAN:     'DE',
    Language.FRENCH:     'FR',
    Language.CATALAN:    'CA',
    Language.PORTUGUESE: 'PT',
}

MIN_TEXT_LEN = 30

def get_confidences(text):
    """Retorna llista de (codi, confiança) ordenada per confiança desc."""
    if not text or len(text.strip()) < MIN_TEXT_LEN:
        return []
    vals = _detector_raw.compute_language_confidence_values(text)
    return [(v.language, _CODE_MAP.get(v.language, '?'), v.value) for v in vals]


# ── Carrega tots els posts de totes les xarxes ────────────────────────────────
all_posts = []
for fname in ['data/linkedin.json', 'data/instagram.json', 'data/facebook.json']:
    try:
        with open(fname, encoding='utf-8') as f:
            posts = json.load(f)
        all_posts.extend(posts)
        print(f'Carregat {fname}: {len(posts)} posts')
    except FileNotFoundError:
        print(f'SKIP (no trobat): {fname}')

print(f'\nTotal posts: {len(all_posts)}')

# ── Analitza els casos detectats amb confiança baixa ─────────────────────────
ambiguous = []   # diferència < 0.35
confident = []   # diferència >= 0.35
undetected = []  # text curt o None

thresholds_to_test = [0.15, 0.25, 0.35, 0.50]

# Per a cada llindar, quants posts tindrien lang='' vs lang detectat
print('\n── Impacte de cada llindar ─────────────────────────────────────────')
print(f'  {"Llindar":>8} │ {"Detectats":>10} │ {"No detectats":>12} │ {"% detectats":>12}')
print(f'  {"─"*8}─┼─{"─"*10}─┼─{"─"*12}─┼─{"─"*12}')

for thresh in thresholds_to_test:
    detected = 0
    not_detected = 0
    for p in all_posts:
        text = p.get('text', '')
        if not text or len(text.strip()) < MIN_TEXT_LEN:
            not_detected += 1
            continue
        vals = get_confidences(text)
        if len(vals) < 2:
            not_detected += 1
            continue
        top_conf   = vals[0][2]
        sec_conf   = vals[1][2]
        diff = top_conf - sec_conf
        if diff >= thresh:
            detected += 1
        else:
            not_detected += 1
    total = detected + not_detected
    pct = 100 * detected / total if total else 0
    print(f'  {thresh:>8.2f} │ {detected:>10} │ {not_detected:>12} │ {pct:>11.1f}%')


# ── Mostra els casos de conflicte PT↔ES, CA↔ES, EN↔DE ────────────────────────
PAIRS_OF_INTEREST = [('PT', 'ES'), ('ES', 'PT'), ('CA', 'ES'), ('ES', 'CA'), ('EN', 'DE'), ('DE', 'EN')]

print('\n── Casos ambigus per parelles (diferència < 0.35) ───────────────────')
for (lang1, lang2) in PAIRS_OF_INTEREST:
    cases = []
    for p in all_posts:
        text = p.get('text', '')
        if not text or len(text.strip()) < MIN_TEXT_LEN:
            continue
        vals = get_confidences(text)
        if len(vals) < 2:
            continue
        top_lang = vals[0][1]
        sec_lang = vals[1][1]
        diff = vals[0][2] - vals[1][2]
        if top_lang == lang1 and sec_lang == lang2 and diff < 0.35:
            cases.append((diff, text[:100], p.get('network', '?')))
    cases.sort()
    print(f'\n  {lang1} vs {lang2}: {len(cases)} casos ambigus (diff < 0.35)')
    for diff, txt, net in cases[:5]:
        print(f'    [{net}] diff={diff:.3f} → {txt!r}')

# ── Distribució amb llindar 0.35 ──────────────────────────────────────────────
THRESH = 0.35
print(f'\n── Distribució d\'idiomes amb llindar {THRESH} ────────────────────────')
dist = {}
for p in all_posts:
    text = p.get('text', '')
    if not text or len(text.strip()) < MIN_TEXT_LEN:
        dist[''] = dist.get('', 0) + 1
        continue
    vals = get_confidences(text)
    if len(vals) < 2:
        dist[''] = dist.get('', 0) + 1
        continue
    diff = vals[0][2] - vals[1][2]
    if diff >= THRESH:
        lang = vals[0][1]
    else:
        lang = ''
    dist[lang] = dist.get(lang, 0) + 1

for lang, count in sorted(dist.items(), key=lambda x: -x[1]):
    label = lang if lang else '(no detectat)'
    print(f'  {label:>12}: {count}')
