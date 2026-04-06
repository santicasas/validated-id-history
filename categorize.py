"""
categorize.py
Afegeix el camp 'categories' a cada post de tots els JSONs de xarxes socials,
i als JSONs de vídeos (videos_facebook.json, videos_youtube.json).
Basat en detecció per keywords.
"""

import json
import os
import re
from collections import OrderedDict

# ── CATEGORIES I KEYWORDS ──────────────────────────────────────────────────────
CATEGORIES = OrderedDict([
    ('firma_electronica', {
        'label': 'Firma electrónica',
        'kw': [
            'firma electr', 'efirma', 'e-firma', 'esign', 'e-sign',
            'vidsigner', 'vid signer', 'firma digital', 'firmar ',
            'firmado', 'firmada', 'signature', 'electronic sign',
            'sign document', 'firma doc',
        ],
    }),
    ('firma_biometrica', {
        'label': 'Firma biométrica',
        'kw': [
            'biométric', 'biometric', 'firma bio', 'firma bío',
            'biom ', 'biomètric',
        ],
    }),
    ('identidad_digital', {
        'label': 'Identidad Digital',
        'kw': [
            'identidad digital', 'identitat digital', 'digital identity',
            'vididentity', 'vid identity', 'ssi', 'self-sovereign',
            ' did ', '#did', 'eidas', 'eidas2', 'wallet', 'verifiable',
            'credencial', 'credential', 'decentrali',
        ],
    }),
    ('factura_electronica', {
        'label': 'Factura electrónica',
        'kw': [
            'factura electr', 'facturació electr', 'facturacion electr',
            'factura ', 'facturaci', 'einvoice', 'e-invoice',
            'verifactu', 'ticketbai', 'peppol', 'sp4i',
            'efactura', 'pimefactura',
        ],
    }),
    ('salud', {
        'label': 'Salud',
        'kw': [
            'salud', 'salut', 'health', 'hospital', 'clínic', 'clinic',
            'consentimiento inform', 'consentiment inform',
            'sanitari', 'sanitario', 'médic', 'medic', 'farmac',
            'pacient', 'paciente', 'ticsalut', '#salud', '#esalud',
        ],
    }),
    ('administracion_publica', {
        'label': 'Administración pública',
        'kw': [
            'administraci', 'aapp', 'ayuntamiento', 'ajuntament',
            'govern ', 'gobierno', 'sector público', 'public sector',
            'municip', 'diputaci', 'administración pública',
            'paperless', 'sense paper', 'sin papel', 'zero paper',
        ],
    }),
    ('partners', {
        'label': 'Partners',
        'kw': [
            'partner', 'sap ', 'salesforce', 'docuware', 'sage ',
            'colaboraci', 'col·laboraci', 'acuerdo de colabor',
            'alianza', 'integrador', 'reseller', 'distribuidor',
        ],
    }),
    ('eventos', {
        'label': 'Eventos y ferias',
        'kw': [
            'mwc', 'mobile world congress', 'congress', 'congres',
            'feria', 'evento', 'jornada', 'webinar', ' stand ',
            'booth', 'cnis', 'smart country', 'conferenci',
            'ponencia', 'presentaci', 'demo ', '#mwc',
        ],
    }),
    ('blockchain', {
        'label': 'Blockchain',
        'kw': [
            'blockchain', 'dlt', 'distributed ledger',
            '#blockchain', 'web3',
        ],
    }),
    ('corporativo', {
        'label': 'Corporativo',
        'kw': [
            'signaturit', 'adquisici', 'acqui', 'ronda de',
            'financiaci', 'inversió', 'inversión', 'funding',
            'premi ', 'award', 'winner', 'finalist', 'reconoci',
            'premio', 'galardón', 'celebr', 'aniversari', 'aniversario',
            'equipazo', 'nuestro equipo', 'nostre equip',
        ],
    }),
])


def categorize_text(text):
    """Retorna llista de categories detectades en un text."""
    if not text:
        return []
    t = text.lower()
    cats = []
    for key, info in CATEGORIES.items():
        if any(kw.lower() in t for kw in info['kw']):
            cats.append(key)
    # Post-processament: si hi ha 'partners', treure 'corporativo'
    if 'partners' in cats and 'corporativo' in cats:
        cats.remove('corporativo')
    return cats


def process_network_json(path):
    """Afegeix 'categories' a cada post d'un JSON de xarxa social."""
    if not os.path.exists(path):
        print(f'  ⚠ No trobat: {path}')
        return 0
    with open(path, encoding='utf-8') as f:
        posts = json.load(f)
    changed = 0
    for p in posts:
        cats = categorize_text(p.get('text', ''))
        if p.get('categories') != cats:
            p['categories'] = cats
            changed += 1
        elif 'categories' not in p:
            p['categories'] = cats
            changed += 1
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    n_with_cats = sum(1 for p in posts if p.get('categories'))
    print(f'  ✓ {path}: {len(posts)} posts, {n_with_cats} amb categories')
    return len(posts)


def process_videos_facebook(path):
    """Afegeix 'categories' als vídeos de videos_facebook.json."""
    if not os.path.exists(path):
        print(f'  ⚠ No trobat: {path}')
        return
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    for key, v in data.items():
        text = v.get('title', '')
        v['categories'] = categorize_text(text)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'  ✓ {path}: {len(data)} vídeos processats')


def process_videos_youtube(path):
    """Afegeix 'categories' als vídeos de videos_youtube.json."""
    if not os.path.exists(path):
        print(f'  ⚠ No trobat: {path}')
        return
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    for v in data:
        text = (v.get('title', '') + ' ' + v.get('description', '')).strip()
        v['categories'] = categorize_text(text)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'  ✓ {path}: {len(data)} vídeos processats')


def print_stats(posts_all):
    """Mostra estadístiques de categories."""
    from collections import Counter
    counts = Counter()
    for p in posts_all:
        for c in p.get('categories', []):
            counts[c] += 1
    total = len(posts_all)
    print(f'\n── Estadístiques de categories ({total} posts) ────────')
    for key, info in CATEGORIES.items():
        n = counts.get(key, 0)
        bar = '█' * (n * 30 // max(counts.values(), default=1))
        print(f'  {info["label"]:<25} {n:5d} ({n*100//total:2d}%)  {bar}')
    no_cat = sum(1 for p in posts_all if not p.get('categories'))
    print(f'\n  Sense categoria: {no_cat} ({no_cat*100//total}%)')


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print('Categoritzant posts de xarxes socials...\n')

    all_posts = []
    for net in ['linkedin', 'instagram', 'facebook', 'twitter']:
        path = f'data/{net}.json'
        process_network_json(path)
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                all_posts.extend(json.load(f))

    print('\nCategoritzant vídeos...\n')
    process_videos_facebook('data/videos_facebook.json')
    process_videos_youtube('data/videos_youtube.json')

    print_stats(all_posts)
    print('\nFet.')
