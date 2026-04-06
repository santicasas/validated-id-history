"""
generate.py
Llegeix els fitxers data/*.json i genera les pàgines HTML del projecte.

Pàgines generades:
  - linkedin.html   Posts de LinkedIn paginats
  - instagram.html  Posts d'Instagram paginats
  - imatges.html    Galeria unificada d'imatges de totes les xarxes

Ús:
  python generate.py
"""

import json
import os
from html import escape
from datetime import datetime, timezone

# ── CONFIGURACIÓ ──────────────────────────────────────────────────────────────
NETWORKS_AVAILABLE = ['linkedin', 'instagram', 'facebook', 'twitter']

CATEGORIES = {
    'firma_electronica':     'Firma electrónica',
    'firma_biometrica':      'Firma biométrica',
    'identidad_digital':     'Identidad Digital',
    'factura_electronica':   'Factura electrónica',
    'salud':                 'Salud',
    'administracion_publica':'Administración pública',
    'partners':              'Partners',
    'eventos':               'Eventos y ferias',
    'blockchain':            'Blockchain',
    'corporativo':           'Corporativo',
}

CONTENT_TYPE_LABELS = {
    'article':    '📰 Artículo',
    'media':      '📷 Imagen',
    'multiImage': '🖼️ Galería',
    'none':       '📝 Texto',
    'reference':  '🔗 Referencia',
    'carousel':   '🎠 Carrusel',
    'poll':       '📊 Encuesta',
    # Instagram
    'image':      '📷 Imagen',
    'sidecar':    '🖼️ Galería',
    'video':      '🎬 Vídeo',
    # Facebook
    'photo':      '📷 Foto',
    'multiPhoto': '🖼️ Álbum',
}

NETWORK_TITLES = {
    'linkedin':  'LinkedIn · Publicaciones',
    'instagram': 'Instagram · Publicaciones',
    'facebook':  'Facebook · Publicaciones',
}

NETWORK_PAGE_NAMES = {
    'linkedin':  'LinkedIn',
    'instagram': 'Instagram',
    'facebook':  'Facebook',
}

NETWORK_LABELS = {
    'linkedin':  '💼 LinkedIn',
    'twitter':   '𝕏 Twitter/X',
    'instagram': '📷 Instagram',
    'facebook':  '📘 Facebook',
}

NETWORK_BADGE_COLORS = {
    'linkedin':  '#0077b5',
    'twitter':   '#1da1f2',
    'instagram': '#c13584',
    'facebook':  '#1877f2',
}

PAGE_SIZE = 50   # posts per pàgina a linkedin.html


# ── UTILITATS ─────────────────────────────────────────────────────────────────
def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def esc(text):
    return escape(str(text), quote=True)

def truncate(text, length=280):
    if len(text) <= length:
        return text
    return text[:length].rstrip() + '…'

def date_sort_key(p):
    """Clau d'ordenació cronològica. Suporta YYYY-MM-DD i DD/MM/YYYY."""
    d = p['date']
    try:
        if len(d) == 10 and d[4] == '-':
            return d.replace('-', '')           # YYYY-MM-DD → YYYYMMDD (ja ordenable)
        elif len(d) == 10 and d[2] == '/':
            return d[6:] + d[3:5] + d[:2]      # DD/MM/YYYY → YYYYMMDD
        return d
    except Exception:
        return '00000000'

def get_years(posts):
    return sorted(set(p['year'] for p in posts), reverse=True)   # de més recent a més antic


# ── COMPONENTS HTML COMUNS ─────────────────────────────────────────────────────
COMMON_CSS = """
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  [hidden] { display: none !important; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #151A35;
    color: #ccd6f6;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  header {
    background: #0d1229;
    border-bottom: 3px solid #00BF71;
    padding: 1rem 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    position: sticky;
    top: 0;
    z-index: 100;
  }

  .logo-area { display: flex; align-items: center; gap: 0.5rem; }
  .logo-image { height: 30px; width: auto; display: block; }
  .header-subtitle { font-size: 0.85rem; color: #8892b0; margin-left: 0.5rem; }

  .header-network-nav { margin-left: auto; display: flex; gap: 0.5rem; }
  .header-network-btn {
    background: transparent;
    border: 1px solid #2a3a5a;
    color: #ccd6f6;
    border-radius: 6px;
    padding: 0.35rem 0.7rem;
    font-size: 0.8rem;
    font-weight: 700;
    cursor: pointer;
    text-decoration: none;
  }
  .header-network-btn:hover { border-color: #00BF71; color: #00BF71; }
  .header-network-btn.active {
    background: #00BF71; border-color: #00BF71; color: #0d1229; cursor: default;
  }

  .layout { display: flex; flex: 1; min-height: 0; }

  .sidebar {
    width: 220px; min-width: 220px;
    background: #0d1229;
    padding: 1.5rem 1rem;
    position: sticky;
    top: 67px;
    height: calc(100vh - 67px);
    overflow-y: auto;
    border-right: 1px solid #2a3a5a;
  }

  .filter-section { border-bottom: 1px solid #1e2a4a; }
  .filter-section-header {
    display: flex; align-items: center;
    padding: 0.5rem 0; cursor: pointer; user-select: none;
  }
  .filter-section-title {
    font-size: 0.7rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1px;
    color: #00BF71; flex: 1;
  }
  .filter-section-badge {
    font-size: 0.65rem; background: #00BF71; color: #0d1229;
    border-radius: 10px; padding: 0 6px; font-weight: 700;
    margin-right: 0.3rem; min-width: 18px; text-align: center;
  }
  .filter-section-arrow {
    font-size: 0.55rem; color: #8892b0;
    transition: transform 0.2s; display: inline-block;
  }
  .filter-section-arrow.open { transform: rotate(90deg); }
  .filter-section-body { display: none; padding-bottom: 0.5rem; }
  .filter-section-body.open { display: block; }
  .filter-chips { display: flex; flex-wrap: wrap; gap: 4px; padding-top: 2px; }
  .filter-chip {
    background: #1a2a4a; color: #8892b0;
    border: 1px solid #2a3a5a; border-radius: 4px;
    font-size: 0.7rem; font-weight: 600;
    padding: 0.2rem 0.45rem; cursor: pointer;
    user-select: none; transition: all 0.15s; line-height: 1.4;
  }
  .filter-chip:hover { border-color: #00BF71; color: #ccd6f6; }
  .filter-chip.active { background: #00BF71; color: #0d1229; border-color: #00BF71; }
  .clear-btn {
    width: 100%; background: transparent;
    border: 1px solid #2a3a5a; color: #8892b0;
    padding: 0.4rem 0.8rem; border-radius: 4px;
    cursor: pointer; font-size: 0.82rem; margin-top: 0.8rem; transition: all 0.2s;
  }
  .clear-btn:hover { border-color: #00BF71; color: #00BF71; }

  main { flex: 1; padding: 1.5rem; overflow-y: auto; min-width: 0; }

  .results-bar { font-size: 0.85rem; color: #8892b0; margin-bottom: 1rem; }
  .results-bar span { color: #00BF71; font-weight: 700; }

  .badge {
    font-size: 0.68rem; font-weight: 600;
    padding: 0.12rem 0.45rem; border-radius: 3px; white-space: nowrap;
  }
  .badge-year { background: #00BF71; color: #0d1229; }
  .badge-cat {
    background: #1a2a4a; color: #7dd3fc;
    border: 1px solid #2563eb; border-radius: 3px;
    font-size: 0.62rem; font-weight: 600;
    padding: 0.1rem 0.4rem; white-space: nowrap;
  }

  footer {
    background: #0d1229; border-top: 1px solid #2a3a5a;
    text-align: center; padding: 1rem; font-size: 0.8rem; color: #8892b0;
  }
  footer a { color: #00BF71; text-decoration: none; }

  @media (max-width: 768px) {
    header { padding: 0.6rem 1rem; flex-wrap: wrap; gap: 0.4rem; }
    .header-subtitle { display: none; }
    .header-network-nav { margin-left: 0; width: 100%; gap: 0.3rem; flex-wrap: wrap; }
    .header-network-btn { padding: 0.25rem 0.5rem; font-size: 0.72rem; }
    .sidebar { display: none; }
    main { padding: 1rem 0.75rem; }
  }
  @media (max-width: 480px) {
    .header-network-btn { padding: 0.2rem 0.4rem; font-size: 0.68rem; }
  }
"""

def html_header(subtitle, active_page):
    nav_pages = [
        ('historia.html',  'Historia'),
        ('imatges.html',   'Imágenes'),
        ('videos.html',    'Vídeos'),
        ('linkedin.html',  'LinkedIn'),
        ('twitter.html',   'Twitter'),
        ('facebook.html',  'Facebook'),
        ('instagram.html', 'Instagram'),
    ]
    buttons = ''
    for href, label in nav_pages:
        if label == active_page:
            buttons += f'<button class="header-network-btn active">{label}</button>'
        else:
            buttons += f'<a href="{href}" class="header-network-btn">{label}</a>'
    return f"""<header>
  <div class="logo-area">
    <a href="index.html" title="Volver al inicio">
      <img class="logo-image" src="assets/validated-id-logo-white-text-alt.webp" alt="Validated ID">
    </a>
    <span class="header-subtitle">{subtitle}</span>
  </div>
  <div class="header-network-nav">{buttons}</div>
</header>"""

def html_footer():
    return """<footer>
  Archivo histórico &middot; Media alojado en <a href="https://archive.org" target="_blank">Internet Archive</a> &middot; Validated ID (2012&ndash;2026)
</footer>"""

LANG_LABELS = {
    'ES': 'ES 🇪🇸', 'EN': 'EN 🇬🇧', 'DE': 'DE 🇩🇪',
    'FR': 'FR 🇫🇷', 'CA': 'CA 🟨', 'PT': 'PT 🇵🇹',
}
LANG_ORDER = ['ES', 'EN', 'DE', 'FR', 'CA', 'PT']

def filter_section_html(title, chips_html, start_open=False):
    """Genera una secció de filtre col·lapsable amb chips."""
    body_cls  = 'filter-section-body' + (' open' if start_open else '')
    arrow_cls = 'filter-section-arrow' + (' open' if start_open else '')
    return (f'<div class="filter-section">\n'
            f'  <div class="filter-section-header" onclick="toggleSection(this)">\n'
            f'    <span class="filter-section-title">{title}</span>\n'
            f'    <span class="filter-section-badge" style="display:none"></span>\n'
            f'    <span class="{arrow_cls}">&#9658;</span>\n'
            f'  </div>\n'
            f'  <div class="{body_cls}">\n'
            f'    <div class="filter-chips">{chips_html}    </div>\n'
            f'  </div>\n'
            f'</div>\n')

def year_filter_html(years):
    chips = ''.join(
        f'<button class="filter-chip" data-type="year" data-value="{y}" onclick="toggleChip(this)">{y}</button>'
        for y in years
    )
    return filter_section_html('Año', chips)

def lang_filter_html(langs):
    langs_sorted = sorted(langs, key=lambda l: LANG_ORDER.index(l) if l in LANG_ORDER else 99)
    chips = ''.join(
        f'<button class="filter-chip" data-type="lang" data-value="{esc(l)}" onclick="toggleChip(this)">{LANG_LABELS.get(l, l)}</button>'
        for l in langs_sorted
    )
    return filter_section_html('Idioma', chips)

def category_filter_html():
    chips = ''.join(
        f'<button class="filter-chip" data-type="category" data-value="{key}" onclick="toggleChip(this)">{label}</button>'
        for key, label in CATEGORIES.items()
    )
    return filter_section_html('Categoría', chips, start_open=True)

def get_langs(posts):
    return sorted(set(p.get('lang','') for p in posts if p.get('lang','')),
                  key=lambda l: LANG_ORDER.index(l) if l in LANG_ORDER else 99)

def network_filter_html(networks):
    """Genera els chips de xarxa/compte per al sidebar d'imatges.html."""
    chips = ''
    for n in networks:
        if n == 'twitter':
            for acc in TWITTER_ACCOUNT_COLORS:
                key   = f'x:{acc}'
                label = f'x:@{acc}'
                chips += f'<button class="filter-chip" data-type="network" data-value="{key}" onclick="toggleChip(this)">{label}</button>'
        else:
            label = NETWORK_LABELS.get(n, n)
            chips += f'<button class="filter-chip" data-type="network" data-value="{n}" onclick="toggleChip(this)">{label}</button>'
    return filter_section_html('Red', chips)


# ── GENERADOR: pàgina per xarxa (LinkedIn, Instagram, ...) ────────────────────
def generate_network_page(network, posts):
    years = get_years(posts)
    langs = get_langs(posts)

    page_name  = NETWORK_PAGE_NAMES.get(network, network.capitalize())
    page_title = NETWORK_TITLES.get(network, f'{page_name} · Publicaciones')

    # Preparem les dades per al JS (text complet, sense truncar)
    js_posts = []
    for p in posts:
        js_posts.append({
            'anchor':     p['anchor'],
            'date':       p['date'],
            'year':       p['year'],
            'lang':       p.get('lang', ''),
            'type':       p.get('content_type', 'none'),
            'text':       p['text'],
            'images':     p['images'],
            'video':      p.get('video'),
            'url':        p.get('url'),
            'pageRef':    p['page_ref'],
            'categories': p.get('categories', []),
        })

    posts_json = json.dumps(js_posts, ensure_ascii=False, separators=(',', ':'))

    content_type_labels_js = json.dumps(CONTENT_TYPE_LABELS, ensure_ascii=False)

    year_filters  = year_filter_html(years)
    lang_filters  = lang_filter_html(langs)
    cat_filters   = category_filter_html()

    media_chips = ('<button class="filter-chip" data-type="media" data-value="images" onclick="toggleChip(this)">Con imágenes</button>'
                   '<button class="filter-chip" data-type="media" data-value="video" onclick="toggleChip(this)">Con vídeo</button>')
    media_filters = filter_section_html('Contenido', media_chips)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Validated ID — {page_name}</title>
<style>
{COMMON_CSS}

  .post-card {{
    background: #1e2a4a;
    border: 1px solid #2a3a5a;
    border-radius: 8px;
    padding: 1rem 1.1rem;
    margin-bottom: 1rem;
    transition: border-color 0.15s;
    scroll-margin-top: 80px;
  }}
  .post-card:hover {{ border-color: #3a4a6a; }}
  .post-card.highlighted {{
    border-color: #00BF71;
    box-shadow: 0 0 0 2px rgba(0,191,113,0.2);
  }}

  .post-header {{
    display: flex; align-items: center; gap: 0.5rem;
    margin-bottom: 0.6rem; flex-wrap: wrap;
  }}
  .post-date {{ font-size: 0.78rem; color: #8892b0; }}

  .badge-type {{
    font-size: 0.68rem; font-weight: 600;
    padding: 0.12rem 0.45rem; border-radius: 3px;
    background: #2a3a5a; color: #ccd6f6;
    border: 1px solid #3a4a6a;
  }}

  /* ── LAYOUT POST: text esquerra / media dreta ── */
  .post-body {{
    display: flex;
    gap: 1rem;
    align-items: flex-start;
  }}
  .post-text-col {{
    flex: 1;
    min-width: 0;
  }}
  .post-media-col {{
    flex: 0 0 260px;
    width: 260px;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }}

  .post-text {{
    font-size: 0.88rem; color: #ccd6f6;
    line-height: 1.55; white-space: pre-wrap;
    word-break: break-word; margin-bottom: 0.4rem;
  }}
  .post-text.no-text {{ color: #4a5a7a; font-style: italic; }}

  /* Imatges dins la columna de media */
  .post-img-wrap {{
    position: relative; cursor: pointer;
    border-radius: 6px; overflow: hidden;
    border: 1px solid #2a3a5a; width: 100%;
  }}
  .post-img-wrap img {{
    width: 100%; height: 180px; object-fit: cover;
    display: block; transition: opacity 0.3s;
  }}
  .post-img-wrap img.loading {{ opacity: 0; }}
  .post-img-wrap:hover img {{ opacity: 0.85; }}

  /* VÍDEO */
  .post-video-wrap {{
    position: relative; cursor: pointer;
    border-radius: 6px; overflow: hidden;
    border: 1px solid #2a3a5a; width: 100%;
  }}
  .post-video-wrap img {{
    width: 100%; height: 160px; object-fit: cover;
    display: block; transition: opacity 0.3s;
  }}
  .post-video-wrap img.loading {{ opacity: 0; }}
  .post-video-wrap:hover img {{ opacity: 0.75; }}
  .video-play-btn {{
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 52px; height: 52px; border-radius: 50%;
    background: rgba(0,191,113,0.85);
    display: flex; align-items: center; justify-content: center;
    pointer-events: none;
  }}
  .video-play-btn::after {{
    content: '';
    border-style: solid;
    border-width: 10px 0 10px 18px;
    border-color: transparent transparent transparent #0d1229;
    margin-left: 3px;
  }}
  .video-title {{
    font-size: 0.75rem; color: #8892b0;
    padding: 0.4rem 0.5rem;
    background: #0d1229; border-top: 1px solid #2a3a5a;
  }}

  /* LIGHTBOX VÍDEO */
  .lb-video-wrap {{
    width: min(860px, 90vw);
    aspect-ratio: 16/9;
  }}
  .lb-video-wrap iframe {{
    width: 100%; height: 100%; border: none; border-radius: 4px;
  }}

  .img-count-badge {{
    position: absolute; bottom: 6px; right: 6px;
    background: rgba(0,0,0,0.75); color: #fff;
    font-size: 0.7rem; font-weight: 700;
    padding: 0.1rem 0.4rem; border-radius: 3px;
  }}

  .imatges-link {{
    display: inline-block; margin-top: 0.5rem;
    font-size: 0.75rem; color: #00BF71; text-decoration: none;
    opacity: 0.7;
  }}
  .imatges-link:hover {{ opacity: 1; }}

  /* PAGINACIÓ */
  .pagination {{
    display: flex; align-items: center; justify-content: center;
    gap: 0.5rem; padding: 1.5rem 0; flex-wrap: wrap;
  }}
  .page-btn {{
    background: transparent; border: 1px solid #2a3a5a;
    color: #ccd6f6; border-radius: 6px;
    padding: 0.35rem 0.7rem; font-size: 0.85rem;
    cursor: pointer; transition: all 0.2s; min-width: 36px;
  }}
  .page-btn:hover {{ border-color: #00BF71; color: #00BF71; }}
  .page-btn.active {{ background: #00BF71; border-color: #00BF71; color: #0d1229; font-weight: 700; }}
  .page-btn:disabled {{ opacity: 0.3; cursor: default; }}
  .page-info {{ font-size: 0.82rem; color: #8892b0; padding: 0 0.5rem; }}

  /* LIGHTBOX */
  .lightbox {{
    display: none; position: fixed; inset: 0;
    background: rgba(0,0,0,0.92); z-index: 1000;
    align-items: center; justify-content: center;
    flex-direction: column; padding: 2rem;
  }}
  .lightbox.open {{ display: flex; }}
  .lightbox img {{
    max-width: 90vw; max-height: 78vh; object-fit: contain;
    border-radius: 4px; box-shadow: 0 0 60px rgba(0,0,0,0.8);
  }}
  .lightbox-meta {{ margin-top: 1rem; text-align: center; max-width: 600px; }}
  .lightbox-date {{ font-size: 0.8rem; color: #00BF71; font-weight: 700; margin-bottom: 0.4rem; }}
  .lightbox-caption {{ font-size: 0.88rem; color: #ccd6f6; line-height: 1.5; }}
  .lightbox-close {{
    position: absolute; top: 1.5rem; right: 1.5rem;
    background: transparent; border: none; color: #ccd6f6;
    font-size: 2rem; cursor: pointer; line-height: 1;
  }}
  .lightbox-close:hover {{ color: #00BF71; }}
  .lightbox-nav {{
    position: absolute; top: 50%; transform: translateY(-50%);
    background: rgba(255,255,255,0.1); border: none; color: #fff;
    font-size: 2rem; cursor: pointer; padding: 0.5rem 0.8rem; border-radius: 4px;
  }}
  .lightbox-nav:hover {{ background: rgba(0,191,113,0.3); }}
  .lightbox-prev {{ left: 1rem; }}
  .lightbox-next {{ right: 1rem; }}

  @media (max-width: 900px) {{
    .post-body {{ flex-direction: column; }}
    .post-media-col {{ flex: none; width: 100%; flex-direction: row; flex-wrap: wrap; }}
    .post-img-wrap {{ flex: 1; min-width: 140px; }}
    .post-video-wrap {{ flex: 1; min-width: 200px; }}
  }}
  @media (max-width: 600px) {{
    .post-img-wrap img {{ height: 140px; }}
    .post-video-wrap img {{ height: 120px; }}
    .post-text {{ font-size: 0.82rem; }}
  }}
</style>
</head>
<body>

{html_header(page_title, page_name)}

<div class="layout">
  <aside class="sidebar">
    {year_filters}
    {media_filters}
    {lang_filters}
    {cat_filters}
    <button class="clear-btn" onclick="clearFilters()">Borrar filtros</button>
  </aside>

  <main>
    <div class="results-bar"><span id="count">0</span> publicaciones &mdash; página <span id="page-display">1</span></div>
    <div id="posts-container"></div>
    <div class="pagination" id="pagination"></div>
  </main>
</div>

{html_footer()}

<!-- LIGHTBOX -->
<div class="lightbox" id="lightbox">
  <button class="lightbox-close" onclick="closeLightbox()">&times;</button>
  <button class="lightbox-nav lightbox-prev" id="lb-prev" onclick="navLightbox(-1)">&#8249;</button>
  <div id="lb-content"></div>
  <div class="lightbox-meta">
    <div class="lightbox-date" id="lb-date"></div>
    <div class="lightbox-caption" id="lb-caption"></div>
  </div>
  <button class="lightbox-nav lightbox-next" id="lb-next" onclick="navLightbox(1)">&#8250;</button>
</div>

<script>
const POSTS = {posts_json};
const CONTENT_TYPES = {content_type_labels_js};
const CATEGORIES = {json.dumps(CATEGORIES, ensure_ascii=False)};
const PAGE_SIZE = {PAGE_SIZE};

let filtered = [...POSTS];
let currentPage = 0;
let lbImages = [];
let lbVideoUrl = null;
let lbIdx = 0;

// ── FILTRES UI ────────────────────────────────────────────────────────────────
function toggleSection(header) {{
  const body  = header.nextElementSibling;
  const arrow = header.querySelector('.filter-section-arrow');
  body.classList.toggle('open');
  arrow.classList.toggle('open');
}}
function toggleChip(chip) {{
  chip.classList.toggle('active');
  const section = chip.closest('.filter-section');
  const badge   = section.querySelector('.filter-section-badge');
  const n = section.querySelectorAll('.filter-chip.active').length;
  badge.textContent   = n;
  badge.style.display = n ? '' : 'none';
  applyFilters();
}}
function clearFilters() {{
  document.querySelectorAll('.filter-chip.active').forEach(c => c.classList.remove('active'));
  document.querySelectorAll('.filter-section-badge').forEach(b => {{
    b.textContent = ''; b.style.display = 'none';
  }});
  applyFilters();
}}

// ── FILTRES ───────────────────────────────────────────────────────────────────
function applyFilters() {{
  const years  = new Set([...document.querySelectorAll('.filter-chip[data-type=year].active')].map(c => c.dataset.value));
  const media  = new Set([...document.querySelectorAll('.filter-chip[data-type=media].active')].map(c => c.dataset.value));
  const langs  = new Set([...document.querySelectorAll('.filter-chip[data-type=lang].active')].map(c => c.dataset.value));
  const cats   = new Set([...document.querySelectorAll('.filter-chip[data-type=category].active')].map(c => c.dataset.value));
  filtered = POSTS.filter(p => {{
    if (years.size > 0 && !years.has(p.year)) return false;
    if (media.has('images') && p.images.length === 0) return false;
    if (media.has('video')  && !p.video)              return false;
    if (langs.size > 0 && !langs.has(p.lang))         return false;
    if (cats.size  > 0 && !(p.categories || []).some(c => cats.has(c))) return false;
    return true;
  }});
  currentPage = 0;
  renderPage();
}}

// ── RENDER ────────────────────────────────────────────────────────────────────
function renderPage() {{
  const start = currentPage * PAGE_SIZE;
  const pagePosts = filtered.slice(start, start + PAGE_SIZE);
  const container = document.getElementById('posts-container');

  container.innerHTML = pagePosts.map(p => postHTML(p)).join('');

  // Lazy load images
  container.querySelectorAll('img[data-src]').forEach(img => {{
    const observer = new IntersectionObserver(entries => {{
      entries.forEach(e => {{
        if (e.isIntersecting) {{
          img.src = img.dataset.src;
          img.onload = () => img.classList.remove('loading');
          observer.disconnect();
        }}
      }});
    }});
    observer.observe(img);
  }});

  document.getElementById('count').textContent = filtered.length;
  document.getElementById('page-display').textContent = currentPage + 1;
  renderPagination();
}}

function postHTML(p) {{
  const typeLabel = CONTENT_TYPES[p.type] || p.type;
  const textHTML = p.text
    ? `<div class="post-text">${{escHTML(p.text)}}</div>`
    : `<div class="post-text no-text">(sin texto)</div>`;
  const urlHTML = '';

  // Imatges (columna dreta): mostrem totes apilades
  let mediaColHTML = '';
  if (p.images.length > 0) {{
    mediaColHTML += p.images.map((url, i) => `
      <div class="post-img-wrap" onclick="openImgLightbox('${{escAttr(p.anchor)}}', ${{i}})">
        <img data-src="${{url}}" src="" alt="" class="loading">
        ${{i === 0 && p.images.length > 1 ? `<span class="img-count-badge">1/${{p.images.length}}</span>` : ''}}
      </div>`).join('');
  }}

  // Vídeo (miniatura clicable → lightbox amb iframe)
  if (p.video) {{
    mediaColHTML += `
      <div class="post-video-wrap" onclick="openVideoLightbox('${{escAttr(p.anchor)}}')" title="Reproducir vídeo">
        <img data-src="${{p.video.thumbnail_url}}" src="" alt="${{escAttr(p.video.title)}}" class="loading">
        <div class="video-play-btn"></div>
      </div>`;
  }}

  const mediaCol = mediaColHTML
    ? `<div class="post-media-col">${{mediaColHTML}}</div>`
    : '';

  const catBadges = (p.categories || []).map(c => CATEGORIES[c]
    ? `<span class="badge badge-cat">${{escHTML(CATEGORIES[c])}}</span>` : '').join('');

  return `<div class="post-card" id="${{escAttr(p.anchor)}}">
    <div class="post-header">
      <span class="badge badge-year">${{p.year}}</span>
      <span class="badge badge-type">${{typeLabel}}</span>
      <span class="post-date">${{p.date}}</span>
      ${{catBadges}}
    </div>
    <div class="post-body">
      <div class="post-text-col">${{textHTML}}${{urlHTML}}</div>
      ${{mediaCol}}
    </div>
  </div>`;
}}

function escHTML(str) {{
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}
function escAttr(str) {{
  return str.replace(/"/g,'&quot;');
}}

// ── PAGINACIÓ ─────────────────────────────────────────────────────────────────
function renderPagination() {{
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const pag = document.getElementById('pagination');
  if (totalPages <= 1) {{ pag.innerHTML = ''; return; }}

  let html = `<button class="page-btn" onclick="goPage(${{currentPage-1}})" ${{currentPage===0?'disabled':''}}>&#8249;</button>`;

  const range = pageRange(currentPage, totalPages);
  range.forEach(p => {{
    if (p === '…') {{
      html += `<span class="page-info">…</span>`;
    }} else {{
      html += `<button class="page-btn ${{p===currentPage?'active':''}}" onclick="goPage(${{p}})">${{p+1}}</button>`;
    }}
  }});

  html += `<button class="page-btn" onclick="goPage(${{currentPage+1}})" ${{currentPage===totalPages-1?'disabled':''}}>&#8250;</button>`;
  pag.innerHTML = html;
}}

function pageRange(cur, total) {{
  if (total <= 7) return Array.from({{length: total}}, (_, i) => i);
  const pages = new Set([0, total-1, cur, cur-1, cur+1].filter(p => p >= 0 && p < total));
  const sorted = [...pages].sort((a,b) => a-b);
  const result = [];
  sorted.forEach((p, i) => {{
    if (i > 0 && p - sorted[i-1] > 1) result.push('…');
    result.push(p);
  }});
  return result;
}}

function goPage(p) {{
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  if (p < 0 || p >= totalPages) return;
  currentPage = p;
  renderPage();
  window.scrollTo({{top: 0, behavior: 'smooth'}});
}}

// ── LIGHTBOX ──────────────────────────────────────────────────────────────────
function openLightbox(meta, contentHTML, showNav) {{
  document.getElementById('lb-content').innerHTML  = contentHTML;
  document.getElementById('lb-date').textContent    = meta.date;
  document.getElementById('lb-caption').textContent = meta.text || '';
  document.getElementById('lb-prev').style.display  = showNav ? '' : 'none';
  document.getElementById('lb-next').style.display  = showNav ? '' : 'none';
  document.getElementById('lightbox').classList.add('open');
  document.body.style.overflow = 'hidden';
}}

function openImgLightbox(anchor, imgIdx) {{
  const post = POSTS.find(p => p.anchor === anchor);
  if (!post) return;
  lbImages   = post.images;
  lbVideoUrl = null;
  lbIdx      = imgIdx;
  showLbImage(post);
}}

function showLbImage(post) {{
  if (!post) {{
    // Recupera el post actual pel lbImages actiu
    post = POSTS.find(p => p.images === lbImages);
  }}
  openLightbox(
    post,
    `<img src="${{lbImages[lbIdx]}}" alt="" style="max-width:90vw;max-height:75vh;object-fit:contain;border-radius:4px;">`,
    lbImages.length > 1
  );
}}

function openVideoLightbox(anchor) {{
  const post = POSTS.find(p => p.anchor === anchor);
  if (!post || !post.video) return;
  lbImages   = [];
  lbVideoUrl = post.video.embed_url;
  openLightbox(
    post,
    `<div class="lb-video-wrap"><iframe src="${{post.video.embed_url}}" allowfullscreen></iframe></div>`,
    false
  );
}}

function closeLightbox() {{
  // Atura el vídeo eliminant l'iframe
  const wrap = document.querySelector('.lb-video-wrap');
  if (wrap) wrap.innerHTML = '';
  document.getElementById('lightbox').classList.remove('open');
  document.body.style.overflow = '';
}}

function navLightbox(dir) {{
  if (lbImages.length === 0) return;
  lbIdx = (lbIdx + dir + lbImages.length) % lbImages.length;
  const post = POSTS.find(p => p.images === lbImages);
  showLbImage(post);
}}

document.getElementById('lightbox').addEventListener('click', e => {{
  if (e.target === document.getElementById('lightbox')) closeLightbox();
}});

document.addEventListener('keydown', e => {{
  if (!document.getElementById('lightbox').classList.contains('open')) return;
  if (e.key === 'Escape') closeLightbox();
  if (e.key === 'ArrowRight') navLightbox(1);
  if (e.key === 'ArrowLeft') navLightbox(-1);
}});

// ── HASH NAVIGATION ───────────────────────────────────────────────────────────
function navigateToHash() {{
  const hash = window.location.hash.slice(1);
  if (!hash) return;
  const idx = POSTS.findIndex(p => p.anchor === hash);
  if (idx === -1) return;
  currentPage = Math.floor(idx / PAGE_SIZE);
  renderPage();
  setTimeout(() => {{
    const el = document.getElementById(hash);
    if (el) {{
      el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
      el.classList.add('highlighted');
      setTimeout(() => el.classList.remove('highlighted'), 3000);
    }}
  }}, 150);
}}

// ── INIT ──────────────────────────────────────────────────────────────────────
renderPage();
navigateToHash();
</script>
</body>
</html>"""

    return html


# ── GENERADOR: imatges.html ────────────────────────────────────────────────────
def generate_imatges(all_posts):
    """Genera imatges.html amb posts amb imatge de totes les xarxes."""

    posts_with_images = [p for p in all_posts if p['images']]
    years    = get_years(posts_with_images)
    networks = sorted(set(p['network'] for p in posts_with_images))
    langs    = get_langs(posts_with_images)

    # Dades mínimes per al JS
    js_posts = []
    for p in posts_with_images:
        # Per Twitter: network_label mostra el compte (x:@ValidatedID)
        if p['network'] == 'twitter':
            acc = p.get('account', '')
            net_label = f'x:@{acc}' if acc else 'twitter'
            page_ref  = 'twitter.html'
        else:
            net_label = p['network']
            page_ref  = p.get('page_ref', f"{p['network']}.html")
        # filterKey: clau usada pel filtre de xarxa/compte
        if p['network'] == 'twitter':
            filter_key = f"x:{p.get('account','')}"
        else:
            filter_key = p['network']
        # Normalitza imatges: Twitter té [{url, alt}], les altres xarxes tenen strings
        imgs = [img['url'] if isinstance(img, dict) else img for img in p['images']]
        js_posts.append({
            'anchor':     p['anchor'],
            'network':    p['network'],
            'account':    p.get('account', ''),
            'netLabel':   net_label,
            'filterKey':  filter_key,
            'date':       p['date'],
            'year':       p['year'],
            'lang':       p.get('lang', ''),
            'caption':    truncate(p['text'], 200),
            'images':     imgs,
            'pageRef':    page_ref,
            'categories': p.get('categories', []),
        })

    posts_json       = json.dumps(js_posts, ensure_ascii=False, separators=(',', ':'))
    network_labels   = json.dumps(NETWORK_LABELS, ensure_ascii=False)
    network_colors   = json.dumps(NETWORK_BADGE_COLORS, ensure_ascii=False)

    year_filters    = year_filter_html(years)
    network_filters = network_filter_html(networks)
    lang_filters_im = lang_filter_html(langs)
    cat_filters_im  = category_filter_html()

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Validated ID — Archivo de imágenes</title>
<style>
{COMMON_CSS}

  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 1rem;
  }}

  .card {{
    background: #1e2a4a; border: 1px solid #2a3a5a;
    border-radius: 8px; overflow: hidden;
    transition: transform 0.15s, border-color 0.15s;
  }}
  .card:hover {{ transform: translateY(-2px); border-color: #00BF71; }}

  .card-img-wrap {{
    position: relative; width: 100%; padding-bottom: 66%;
    background: #0d1229; overflow: hidden;
  }}
  .card-img-wrap img {{
    position: absolute; top: 0; left: 0;
    width: 100%; height: 100%; object-fit: cover;
    transition: opacity 0.3s; cursor: pointer;
  }}
  .card-img-wrap img.loading {{ opacity: 0; }}

  .multi-badge {{
    position: absolute; bottom: 6px; right: 6px;
    background: rgba(0,0,0,0.75); color: #fff;
    font-size: 0.7rem; font-weight: 700;
    padding: 0.1rem 0.4rem; border-radius: 3px;
    pointer-events: none;
  }}

  .card-body {{ padding: 0.65rem 0.75rem; }}
  .badges {{ display: flex; gap: 0.35rem; margin-bottom: 0.3rem; flex-wrap: wrap; }}

  .badge-network {{
    font-size: 0.68rem; font-weight: 600;
    padding: 0.12rem 0.45rem; border-radius: 3px; color: #fff;
  }}

  .card-date {{
    font-size: 0.72rem; color: #8892b0; margin-bottom: 0.3rem;
  }}

  .card-caption {{
    font-size: 0.78rem; color: #8892b0; line-height: 1.4;
    display: -webkit-box; -webkit-line-clamp: 3;
    -webkit-box-orient: vertical; overflow: hidden;
    margin-bottom: 0.4rem;
  }}
  .card-caption.empty {{ font-style: italic; color: #3a4a6a; }}

  .post-link {{
    font-size: 0.72rem; color: #00BF71;
    text-decoration: none; opacity: 0.7;
  }}
  .post-link:hover {{ opacity: 1; }}

  /* LIGHTBOX */
  .lightbox {{
    display: none; position: fixed; inset: 0;
    background: rgba(0,0,0,0.92); z-index: 1000;
    align-items: center; justify-content: center;
    flex-direction: column; padding: 2rem;
  }}
  .lightbox.open {{ display: flex; }}
  .lightbox img {{
    max-width: 90vw; max-height: 75vh; object-fit: contain;
    border-radius: 4px; box-shadow: 0 0 60px rgba(0,0,0,0.8);
  }}
  .lightbox-meta {{ margin-top: 1rem; text-align: center; max-width: 600px; }}
  .lightbox-date {{ font-size: 0.8rem; color: #00BF71; font-weight: 700; margin-bottom: 0.25rem; }}
  .lightbox-caption {{ font-size: 0.88rem; color: #ccd6f6; line-height: 1.5; margin-bottom: 0.5rem; }}
  .lightbox-post-link {{ font-size: 0.8rem; color: #00BF71; text-decoration: none; }}
  .lightbox-post-link:hover {{ text-decoration: underline; }}
  .lightbox-close {{
    position: absolute; top: 1.5rem; right: 1.5rem;
    background: transparent; border: none; color: #ccd6f6;
    font-size: 2rem; cursor: pointer; line-height: 1;
  }}
  .lightbox-close:hover {{ color: #00BF71; }}
  .lightbox-nav {{
    position: absolute; top: 50%; transform: translateY(-50%);
    background: rgba(255,255,255,0.1); border: none; color: #fff;
    font-size: 2rem; cursor: pointer; padding: 0.5rem 0.8rem; border-radius: 4px;
  }}
  .lightbox-nav:hover {{ background: rgba(0,191,113,0.3); }}
  .lightbox-prev {{ left: 1rem; }}
  .lightbox-next {{ right: 1rem; }}

  @media (max-width: 700px) {{
    .sidebar {{ display: none; }}
    .grid {{ grid-template-columns: repeat(2, 1fr); }}
  }}
  @media (max-width: 400px) {{
    .grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

{html_header('Archivo de imágenes', 'Imágenes')}

<div class="layout">
  <aside class="sidebar">
    {year_filters}
    {network_filters}
    {lang_filters_im}
    {cat_filters_im}
    <button class="clear-btn" onclick="clearFilters()">Borrar filtros</button>
  </aside>

  <main>
    <div class="results-bar"><span id="count">0</span> imágenes</div>
    <div class="grid" id="grid"></div>
  </main>
</div>

{html_footer()}

<!-- LIGHTBOX -->
<div class="lightbox" id="lightbox">
  <button class="lightbox-close" onclick="closeLightbox()">&times;</button>
  <button class="lightbox-nav lightbox-prev" onclick="navLightbox(-1)">&#8249;</button>
  <img id="lb-img" src="" alt="">
  <div class="lightbox-meta">
    <div class="lightbox-date" id="lb-date"></div>
    <div class="lightbox-caption" id="lb-caption"></div>
    <a class="lightbox-post-link" id="lb-link" href="#">&#8594; Ver publicación</a>
  </div>
  <button class="lightbox-nav lightbox-next" onclick="navLightbox(1)">&#8250;</button>
</div>

<script>
const POSTS = {posts_json};
const NETWORK_LABELS = {network_labels};
const NETWORK_COLORS = {network_colors};
const CATEGORIES = {json.dumps(CATEGORIES, ensure_ascii=False)};

let filtered = [...POSTS];
let lbVisible = [];
let lbIdx = 0;

// ── FILTRES UI ────────────────────────────────────────────────────────────────
function toggleSection(header) {{
  const body  = header.nextElementSibling;
  const arrow = header.querySelector('.filter-section-arrow');
  body.classList.toggle('open');
  arrow.classList.toggle('open');
}}
function toggleChip(chip) {{
  chip.classList.toggle('active');
  const section = chip.closest('.filter-section');
  const badge   = section.querySelector('.filter-section-badge');
  const n = section.querySelectorAll('.filter-chip.active').length;
  badge.textContent   = n;
  badge.style.display = n ? '' : 'none';
  applyFilters();
}}
function clearFilters() {{
  document.querySelectorAll('.filter-chip.active').forEach(c => c.classList.remove('active'));
  document.querySelectorAll('.filter-section-badge').forEach(b => {{
    b.textContent = ''; b.style.display = 'none';
  }});
  applyFilters();
}}

// ── FILTRES ───────────────────────────────────────────────────────────────────
function applyFilters() {{
  const years    = new Set([...document.querySelectorAll('.filter-chip[data-type=year].active')].map(c => c.dataset.value));
  const networks = new Set([...document.querySelectorAll('.filter-chip[data-type=network].active')].map(c => c.dataset.value));
  const langs    = new Set([...document.querySelectorAll('.filter-chip[data-type=lang].active')].map(c => c.dataset.value));
  const cats     = new Set([...document.querySelectorAll('.filter-chip[data-type=category].active')].map(c => c.dataset.value));
  filtered = POSTS.filter(p =>
    (years.size    === 0 || years.has(p.year)) &&
    (networks.size === 0 || networks.has(p.filterKey)) &&
    (langs.size    === 0 || langs.has(p.lang)) &&
    (cats.size     === 0 || (p.categories || []).some(c => cats.has(c)))
  );
  renderGrid();
}}

// ── GRID ──────────────────────────────────────────────────────────────────────
function renderGrid() {{
  const grid = document.getElementById('grid');
  grid.innerHTML = filtered.map((p, i) => cardHTML(p, i)).join('');

  // Lazy load
  grid.querySelectorAll('img[data-src]').forEach(img => {{
    const obs = new IntersectionObserver(entries => {{
      entries.forEach(e => {{
        if (e.isIntersecting) {{
          img.src = img.dataset.src;
          img.onload = () => img.classList.remove('loading');
          obs.disconnect();
        }}
      }});
    }}, {{ rootMargin: '200px' }});
    obs.observe(img);
  }});

  lbVisible = filtered;
  document.getElementById('count').textContent = filtered.length;
}}

const TW_ACC_COLORS = {{'ValidatedID':'#1d9bf0','VIDsigner':'#7c3aed','VIDidentity':'#059669'}};

function cardHTML(p, i) {{
  let netColor, netLabel;
  if (p.network === 'twitter' && p.account) {{
    netColor = TW_ACC_COLORS[p.account] || '#1d9bf0';
    netLabel = `x:@${{p.account}}`;
  }} else {{
    netColor = NETWORK_COLORS[p.network] || '#2a3a5a';
    netLabel = p.netLabel || NETWORK_LABELS[p.network] || p.network;
  }}
  const captionClass = p.caption ? 'card-caption' : 'card-caption empty';
  const captionText  = p.caption || '(sin texto)';
  const multiText    = p.images.length > 1 ? `<span class="multi-badge">1/${{p.images.length}}</span>` : '';
  const catBadges    = (p.categories || []).map(c => CATEGORIES[c]
    ? `<span class="badge badge-cat">${{escHTML(CATEGORIES[c])}}</span>` : '').join('');

  return `<div class="card" data-idx="${{i}}">
    <div class="card-img-wrap" onclick="openLightbox(${{i}})">
      <img data-src="${{p.images[0]}}" src="" alt="" class="loading">
      ${{multiText}}
    </div>
    <div class="card-body">
      <div class="badges">
        <span class="badge badge-year">${{p.year}}</span>
        <span class="badge badge-network" style="background:${{netColor}}">${{netLabel}}</span>
        ${{catBadges}}
      </div>
      <div class="card-date">${{p.date}}</div>
      <div class="${{captionClass}}">${{escHTML(captionText)}}</div>
      <a class="post-link" href="${{p.pageRef}}">&#8594; Ver publicación</a>
    </div>
  </div>`;
}}

function escHTML(str) {{
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}

// ── LIGHTBOX ──────────────────────────────────────────────────────────────────
function openLightbox(visIdx) {{
  lbIdx = visIdx;
  showLbPost(lbVisible[lbIdx]);
  document.getElementById('lightbox').classList.add('open');
  document.body.style.overflow = 'hidden';
}}

function showLbPost(p) {{
  document.getElementById('lb-img').src         = p.images[0];
  document.getElementById('lb-date').textContent = p.date;
  document.getElementById('lb-caption').textContent = p.caption || '';
  const link = document.getElementById('lb-link');
  link.href = p.pageRef;
}}

function closeLightbox() {{
  document.getElementById('lightbox').classList.remove('open');
  document.body.style.overflow = '';
}}

function navLightbox(dir) {{
  lbIdx = (lbIdx + dir + lbVisible.length) % lbVisible.length;
  showLbPost(lbVisible[lbIdx]);
}}

document.getElementById('lightbox').addEventListener('click', e => {{
  if (e.target === document.getElementById('lightbox')) closeLightbox();
}});

document.addEventListener('keydown', e => {{
  if (!document.getElementById('lightbox').classList.contains('open')) return;
  if (e.key === 'Escape')     closeLightbox();
  if (e.key === 'ArrowRight') navLightbox(1);
  if (e.key === 'ArrowLeft')  navLightbox(-1);
}});

// ── INIT ──────────────────────────────────────────────────────────────────────
renderGrid();
</script>
</body>
</html>"""

    return html


# ── GENERADOR: videos.html ────────────────────────────────────────────────────
def load_facebook_videos():
    """Carrega i normalitza els vídeos de Facebook."""
    path = 'data/videos_facebook.json'
    if not os.path.exists(path):
        return []
    data = load_json(path)
    result = []
    for filename, v in data.items():
        ts = v.get('timestamp', 0)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        result.append({
            'source':        'facebook',
            'archive_id':    v['archive_id'],
            'embed_url':     v['embed_url'],
            'thumbnail_url': v['thumbnail_url'],
            'title':         v['title'],
            'date':          dt.strftime('%d/%m/%Y'),
            'year':          dt.strftime('%Y'),
            'lang':          v.get('lang', ''),
            'categories':    v.get('categories', []),
        })
    return result


def load_twitter_videos():
    """Extreu vídeos (natius + YouTube) dels posts de Twitter."""
    path = 'data/twitter.json'
    if not os.path.exists(path):
        return []
    posts = load_json(path)
    result = []
    for p in posts:
        video = p.get('video')
        if not video:
            continue
        # Inclou vídeos natius i YouTube (no youtube_external sense arxiu)
        source = video.get('source', '')
        if source not in ('twitter_native', 'youtube'):
            continue
        account = p.get('account', '')
        result.append({
            'source':        f'x:{account}',
            'account':       account,
            'embed_url':     video.get('embed_url', ''),
            'thumbnail_url': video.get('thumbnail_url', ''),
            'title':         video.get('title', '') or p.get('text', '')[:80],
            'date':          p['date'][8:10] + '/' + p['date'][5:7] + '/' + p['date'][:4],
            'year':          p['year'],
            'lang':          p.get('lang', ''),
            'categories':    p.get('categories', []),
        })
    return result


def load_linkedin_videos():
    """Extreu vídeos natius dels posts de LinkedIn."""
    path = 'data/linkedin.json'
    if not os.path.exists(path):
        return []
    posts = load_json(path)
    result = []
    for p in posts:
        video = p.get('video')
        if not video:
            continue
        if 'embed/validatedid-linkedin-media' not in (video.get('embed_url') or ''):
            continue
        result.append({
            'source':        'linkedin',
            'embed_url':     video['embed_url'],
            'thumbnail_url': video['thumbnail_url'],
            'title':         video.get('title', '') or p.get('text', '')[:80],
            'date':          p['date'][8:10] + '/' + p['date'][5:7] + '/' + p['date'][:4],
            'year':          p['year'],
            'lang':          p.get('lang', ''),
            'categories':    p.get('categories', []),
        })
    return result


def generate_videos():
    """Genera videos.html combinant YouTube, Facebook, Twitter i LinkedIn."""
    # Carrega vídeos de YouTube
    yt_videos = []
    if os.path.exists('data/videos_youtube.json'):
        yt_videos = load_json('data/videos_youtube.json')
        for v in yt_videos:
            v.setdefault('source', 'youtube')

    # Carrega vídeos de Facebook
    fb_videos = load_facebook_videos()

    # Carrega vídeos de Twitter
    tw_videos = load_twitter_videos()

    # Carrega vídeos natius de LinkedIn
    li_videos = load_linkedin_videos()

    all_videos = yt_videos + fb_videos + tw_videos + li_videos

    # Ordena per data descendent (YYYY-MM-DD key)
    def sort_key(v):
        d = v['date']  # DD/MM/YYYY
        try:
            return d[6:10] + d[3:5] + d[0:2]
        except Exception:
            return '00000000'

    all_videos.sort(key=sort_key, reverse=True)

    years = sorted(set(v['year'] for v in all_videos), reverse=True)
    langs = sorted(set(v['lang'] for v in all_videos if v['lang']))

    videos_json = json.dumps(all_videos, ensure_ascii=False, separators=(',', ':'))

    year_filters_html = year_filter_html(years)
    lang_filters_html = lang_filter_html(langs)
    cat_filters_html  = category_filter_html()

    source_chips = (
        '<button class="filter-chip" data-type="source" data-value="youtube" onclick="toggleChip(this)">&#9654; YouTube</button>'
        '<button class="filter-chip" data-type="source" data-value="linkedin" onclick="toggleChip(this)">LinkedIn</button>'
        '<button class="filter-chip" data-type="source" data-value="facebook" onclick="toggleChip(this)">Facebook</button>'
        '<button class="filter-chip" data-type="source" data-value="x:ValidatedID" onclick="toggleChip(this)">x:@ValidatedID</button>'
        '<button class="filter-chip" data-type="source" data-value="x:VIDsigner" onclick="toggleChip(this)">x:@VIDsigner</button>'
        '<button class="filter-chip" data-type="source" data-value="x:VIDidentity" onclick="toggleChip(this)">x:@VIDidentity</button>'
    )
    source_filters_html = filter_section_html('Fuente', source_chips)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Validated ID — Vídeos</title>
<style>
{COMMON_CSS}

  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1rem;
  }}

  .card {{
    background: #1e2a4a; border: 1px solid #2a3a5a;
    border-radius: 8px; overflow: hidden;
    transition: transform 0.15s, border-color 0.15s;
    cursor: pointer;
  }}
  .card:hover {{ transform: translateY(-2px); border-color: #00BF71; }}

  .video-wrap {{
    position: relative; width: 100%; padding-bottom: 56.25%;
    background: #0d1229; overflow: hidden;
  }}
  .video-wrap img {{
    position: absolute; top: 0; left: 0;
    width: 100%; height: 100%; object-fit: cover;
    transition: opacity 0.3s;
  }}
  .video-wrap img.loading {{ opacity: 0; }}
  .card:hover .video-wrap img {{ opacity: 0.75; }}

  .play-btn {{
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 52px; height: 52px; border-radius: 50%;
    background: rgba(0,191,113,0.85);
    display: flex; align-items: center; justify-content: center;
    pointer-events: none;
  }}
  .play-btn::after {{
    content: '';
    border-style: solid;
    border-width: 10px 0 10px 18px;
    border-color: transparent transparent transparent #0d1229;
    margin-left: 3px;
  }}

  .card-body {{ padding: 0.75rem; }}
  .badges {{ display: flex; gap: 0.35rem; margin-bottom: 0.4rem; flex-wrap: wrap; }}

  .badge-source-yt {{ background: #ff0000; color: #fff; }}
  .badge-source-fb {{ background: #1877f2; color: #fff; }}
  .badge-lang {{ background: #2a3a5a; color: #ccd6f6; border: 1px solid #3a4a6a; }}

  .card-title {{
    font-size: 0.88rem; color: #e6f0ff;
    line-height: 1.4; margin-bottom: 0.3rem;
    display: -webkit-box; -webkit-line-clamp: 3;
    -webkit-box-orient: vertical; overflow: hidden;
  }}
  .card-date {{ font-size: 0.75rem; color: #8892b0; }}

  /* LIGHTBOX */
  .lightbox {{
    display: none; position: fixed; inset: 0;
    background: rgba(0,0,0,0.92); z-index: 1000;
    align-items: center; justify-content: center;
    flex-direction: column; padding: 2rem;
  }}
  .lightbox.open {{ display: flex; }}
  .lb-video-wrap {{
    width: min(860px, 90vw);
    aspect-ratio: 16/9;
  }}
  .lb-video-wrap iframe {{
    width: 100%; height: 100%; border: none; border-radius: 4px;
  }}
  .lightbox-meta {{ margin-top: 1rem; text-align: center; max-width: 700px; }}
  .lightbox-title {{ font-size: 1rem; color: #e6f0ff; font-weight: 600; margin-bottom: 0.3rem; }}
  .lightbox-date {{ font-size: 0.8rem; color: #00BF71; }}
  .lightbox-close {{
    position: absolute; top: 1.5rem; right: 1.5rem;
    background: transparent; border: none; color: #ccd6f6;
    font-size: 2rem; cursor: pointer; line-height: 1;
  }}
  .lightbox-close:hover {{ color: #00BF71; }}

  @media (max-width: 700px) {{
    .sidebar {{ display: none; }}
    .grid {{ grid-template-columns: repeat(2, 1fr); }}
  }}
  @media (max-width: 400px) {{
    .grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

{html_header('Vídeos', 'Vídeos')}

<div class="layout">
  <aside class="sidebar">
    {year_filters_html}
    {source_filters_html}
    {lang_filters_html}
    {cat_filters_html}
    <button class="clear-btn" onclick="clearFilters()">Borrar filtros</button>
  </aside>

  <main>
    <div class="results-bar"><span id="count">0</span> vídeos</div>
    <div class="grid" id="grid"></div>
  </main>
</div>

{html_footer()}

<!-- LIGHTBOX -->
<div class="lightbox" id="lightbox">
  <button class="lightbox-close" onclick="closeLightbox()">&times;</button>
  <div id="lb-content"></div>
  <div class="lightbox-meta">
    <div class="lightbox-title" id="lb-title"></div>
    <div class="lightbox-date"  id="lb-date"></div>
  </div>
</div>

<script>
const VIDEOS = {videos_json};
const CATEGORIES = {json.dumps(CATEGORIES, ensure_ascii=False)};

let filtered = [...VIDEOS];

function toggleSection(header) {{
  const body  = header.nextElementSibling;
  const arrow = header.querySelector('.filter-section-arrow');
  body.classList.toggle('open');
  arrow.classList.toggle('open');
}}
function toggleChip(chip) {{
  chip.classList.toggle('active');
  const section = chip.closest('.filter-section');
  const badge   = section.querySelector('.filter-section-badge');
  const n = section.querySelectorAll('.filter-chip.active').length;
  badge.textContent   = n;
  badge.style.display = n ? '' : 'none';
  applyFilters();
}}
function clearFilters() {{
  document.querySelectorAll('.filter-chip.active').forEach(c => c.classList.remove('active'));
  document.querySelectorAll('.filter-section-badge').forEach(b => {{
    b.textContent = ''; b.style.display = 'none';
  }});
  applyFilters();
}}

function applyFilters() {{
  const years   = new Set([...document.querySelectorAll('.filter-chip[data-type=year].active')].map(c => c.dataset.value));
  const sources = new Set([...document.querySelectorAll('.filter-chip[data-type=source].active')].map(c => c.dataset.value));
  const langs   = new Set([...document.querySelectorAll('.filter-chip[data-type=lang].active')].map(c => c.dataset.value));
  const cats    = new Set([...document.querySelectorAll('.filter-chip[data-type=category].active')].map(c => c.dataset.value));
  filtered = VIDEOS.filter(v => {{
    if (years.size   > 0 && !years.has(v.year))     return false;
    if (sources.size > 0 && !sources.has(v.source)) return false;
    if (langs.size   > 0 && !langs.has(v.lang))     return false;
    if (cats.size    > 0 && !(v.categories || []).some(c => cats.has(c))) return false;
    return true;
  }});
  renderGrid();
}}

function escHTML(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}
function escAttr(s) {{
  return String(s).replace(/"/g,'&quot;');
}}

const TW_COLORS = {{'ValidatedID':'#1d9bf0','VIDsigner':'#7c3aed','VIDidentity':'#059669'}};

function cardHTML(v, i) {{
  let srcBadge;
  if (v.source === 'youtube') {{
    srcBadge = '<span class="badge badge-year badge-source-yt">YouTube</span>';
  }} else if (v.source === 'linkedin') {{
    srcBadge = '<span class="badge" style="background:#0077b5;color:#fff">LinkedIn</span>';
  }} else if (v.source === 'facebook') {{
    srcBadge = '<span class="badge badge-year badge-source-fb">Facebook</span>';
  }} else if (v.account) {{
    const col = TW_COLORS[v.account] || '#1d9bf0';
    srcBadge = `<span class="badge" style="background:${{col}};color:#fff">x:@${{escHTML(v.account)}}</span>`;
  }} else {{
    srcBadge = '';
  }}
  const langBadge = v.lang
    ? `<span class="badge badge-lang">${{escHTML(v.lang)}}</span>`
    : '';
  const catBadges = (v.categories || []).map(c => CATEGORIES[c]
    ? `<span class="badge badge-cat">${{escHTML(CATEGORIES[c])}}</span>` : '').join('');
  return `<div class="card" onclick="openVideo(${{i}})">
    <div class="video-wrap">
      <img data-src="${{escAttr(v.thumbnail_url)}}" src="" alt="${{escAttr(v.title)}}" class="loading">
      <div class="play-btn"></div>
    </div>
    <div class="card-body">
      <div class="badges">
        <span class="badge badge-year">${{escHTML(v.year)}}</span>
        ${{srcBadge}}
        ${{langBadge}}
        ${{catBadges}}
      </div>
      <div class="card-title">${{escHTML(v.title)}}</div>
      <div class="card-date">${{escHTML(v.date)}}</div>
    </div>
  </div>`;
}}

function renderGrid() {{
  const grid = document.getElementById('grid');
  grid.innerHTML = filtered.map((v, i) => cardHTML(v, i)).join('');

  // Lazy load
  grid.querySelectorAll('img[data-src]').forEach(img => {{
    const obs = new IntersectionObserver(entries => {{
      entries.forEach(e => {{
        if (e.isIntersecting) {{
          img.src = img.dataset.src;
          img.onload = () => img.classList.remove('loading');
          obs.disconnect();
        }}
      }});
    }}, {{ rootMargin: '200px' }});
    obs.observe(img);
  }});

  document.getElementById('count').textContent = filtered.length;
}}

function openVideo(filteredIdx) {{
  const v = filtered[filteredIdx];
  document.getElementById('lb-content').innerHTML =
    `<div class="lb-video-wrap"><iframe src="${{escAttr(v.embed_url)}}" allowfullscreen></iframe></div>`;
  document.getElementById('lb-title').textContent = v.title;
  document.getElementById('lb-date').textContent  = v.date;
  document.getElementById('lightbox').classList.add('open');
  document.body.style.overflow = 'hidden';
}}

function closeLightbox() {{
  const wrap = document.querySelector('.lb-video-wrap');
  if (wrap) wrap.innerHTML = '';
  document.getElementById('lightbox').classList.remove('open');
  document.body.style.overflow = '';
}}

document.getElementById('lightbox').addEventListener('click', e => {{
  if (e.target === document.getElementById('lightbox')) closeLightbox();
}});

document.addEventListener('keydown', e => {{
  if (!document.getElementById('lightbox').classList.contains('open')) return;
  if (e.key === 'Escape') closeLightbox();
}});

renderGrid();
</script>
</body>
</html>"""

    return html


# ── TWITTER ───────────────────────────────────────────────────────────────────
TWITTER_ACCOUNTS = ['ValidatedID', 'VIDsigner', 'VIDidentity']

TWITTER_ACCOUNT_COLORS = {
    'ValidatedID': '#1d9bf0',
    'VIDsigner':   '#7c3aed',
    'VIDidentity': '#059669',
}

def account_filter_html(accounts):
    chips = ''.join(
        f'<button class="filter-chip" data-type="account" data-value="{esc(acc)}" onclick="toggleChip(this)">x:@{esc(acc)}</button>'
        for acc in accounts
    )
    return filter_section_html('Cuenta', chips)


def generate_twitter_page(posts):
    years    = get_years(posts)
    langs    = get_langs(posts)
    accounts = TWITTER_ACCOUNTS

    js_posts = []
    for p in posts:
        video = p.get('video') or {}
        js_posts.append({
            'id':           p['id'],
            'anchor':       p['anchor'],
            'account':      p.get('account', ''),
            'date':         p['date'],
            'year':         p['year'],
            'text':         p.get('text', ''),
            'lang':         p.get('lang', ''),
            'images':       p.get('images', []),
            'video':        video,
            'url':          p.get('url', ''),
            'content_type': p.get('content_type', 'text'),
            'categories':   p.get('categories', []),
        })

    posts_json   = json.dumps(js_posts, ensure_ascii=False, separators=(',', ':'))
    year_filters = year_filter_html(years)
    acc_filters  = account_filter_html(accounts)
    lang_filters = lang_filter_html(langs)
    cat_filters  = category_filter_html()
    total        = len(posts)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Validated ID — Twitter/X</title>
<style>
{COMMON_CSS}
  .post-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
  }}
  .post-card {{
    background: #1e2a4a; border: 1px solid #2a3a5a; border-radius: 8px;
    overflow: hidden; display: flex; flex-direction: column;
    transition: transform 0.15s, border-color 0.15s;
  }}
  .post-card:hover {{ transform: translateY(-2px); border-color: #00BF71; }}
  .media-wrap {{
    position: relative; width: 100%; padding-bottom: 56.25%;
    background: #0d1229; overflow: hidden; cursor: pointer;
  }}
  .media-wrap img {{
    position: absolute; top: 0; left: 0;
    width: 100%; height: 100%; object-fit: cover;
  }}
  .media-wrap .play-overlay {{
    position: absolute; inset: 0; display: flex;
    align-items: center; justify-content: center;
    background: rgba(0,0,0,.35);
    font-size: 3rem; color: rgba(255,255,255,.9);
    opacity: 0; transition: opacity .2s;
  }}
  .media-wrap:hover .play-overlay {{ opacity: 1; }}
  .post-body {{ padding: 10px 12px; display: flex; flex-direction: column; gap: 6px; flex: 1; }}
  .post-badges {{ display: flex; gap: 5px; flex-wrap: wrap; align-items: center; }}
  .badge-year {{
    background: #21262d; color: #7d8590; border: 1px solid #30363d;
    border-radius: 4px; padding: 1px 6px; font-size: 11px; font-weight: 600;
  }}
  .badge-account {{
    border-radius: 4px; padding: 1px 7px; font-size: 11px; font-weight: 600; color: #fff;
  }}
  .badge-lang {{
    background: #21262d; color: #adbac7; border: 1px solid #30363d;
    border-radius: 4px; padding: 1px 6px; font-size: 10px;
  }}
  .post-text {{ font-size: 13px; color: #adbac7; line-height: 1.5; }}
  .post-text a {{ color: #58a6ff; text-decoration: none; }}
  .post-date {{ font-size: 11px; color: #6e7681; margin-top: auto; padding-top: 4px; }}
  .post-link {{ font-size: 11px; color: #58a6ff; }}
  /* Lightbox */
  .lightbox-overlay {{
    display: none; position: fixed; inset: 0; background: rgba(0,0,0,.88);
    z-index: 1000; align-items: center; justify-content: center;
  }}
  .lightbox-overlay.open {{ display: flex; }}
  .lightbox-inner {{
    position: relative; width: 90vw; max-width: 960px; aspect-ratio: 16/9;
    background: #000;
  }}
  .lightbox-inner iframe {{ width: 100%; height: 100%; border: none; }}
  .lightbox-close {{
    position: absolute; top: -36px; right: 0; background: none; border: none;
    color: #fff; font-size: 28px; cursor: pointer; line-height: 1;
  }}
  @media (max-width: 600px) {{
    .post-grid {{ grid-template-columns: repeat(2, 1fr); }}
  }}
  @media (max-width: 380px) {{
    .post-grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
{html_header('Twitter/X', 'Twitter')}
<div class="layout">
  <aside class="sidebar">
    {year_filters}
    {acc_filters}
    {lang_filters}
    {cat_filters}
    <button class="clear-btn" onclick="clearFilters()">Borrar filtros</button>
  </aside>
  <main>
    <div class="results-header">
      <span id="results-count">{total} tweets</span>
    </div>
    <div class="post-grid" id="grid"></div>
    <div class="pagination" id="pagination"></div>
  </main>
</div>

<!-- Lightbox -->
<div class="lightbox-overlay" id="lightbox" onclick="closeLightbox(event)">
  <div class="lightbox-inner">
    <button class="lightbox-close" onclick="closeLightbox()">&#x2715;</button>
    <iframe id="lightbox-iframe" src="" allowfullscreen
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture">
    </iframe>
  </div>
</div>

<script>
const POSTS = {posts_json};
const PAGE_SIZE = 50;
let filtered = [];
let currentPage = 1;

const ACCOUNT_COLORS = {json.dumps(TWITTER_ACCOUNT_COLORS)};
const LANG_LABELS = {json.dumps(LANG_LABELS)};
const CATEGORIES = {json.dumps(CATEGORIES, ensure_ascii=False)};

function escHTML(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

function fmtDate(d) {{
  if (!d) return '';
  const [y,m,day] = d.split('-');
  return `${{day}}/${{m}}/${{y}}`;
}}

function accountBadge(acc) {{
  const color = ACCOUNT_COLORS[acc] || '#666';
  return `<span class="badge-account" style="background:${{color}}">x:@${{escHTML(acc)}}</span>`;
}}

function postHTML(p) {{
  const color = ACCOUNT_COLORS[p.account] || '#666';
  const lang  = p.lang ? `<span class="badge-lang">${{LANG_LABELS[p.lang] || p.lang}}</span>` : '';

  let mediaHTML = '';
  if (p.video && p.video.thumbnail_url) {{
    const src   = p.video.source === 'twitter_native'
      ? p.video.embed_url
      : (p.video.embed_url || p.video.embed_url);
    const thumb = p.video.thumbnail_url;
    mediaHTML = `
      <div class="media-wrap" onclick="openLightbox('${{escHTML(src)}}')">
        <img src="${{escHTML(thumb)}}" loading="lazy" alt="">
        <div class="play-overlay">&#9654;</div>
      </div>`;
  }} else if (p.images && p.images.length > 0) {{
    mediaHTML = `
      <div class="media-wrap" style="cursor:default">
        <img src="${{escHTML(p.images[0].url)}}" loading="lazy" alt="">
      </div>`;
  }}

  const tweetUrl = p.url || '#';
  const text = escHTML(p.text).replace(/\\n/g, '<br>');

  const catBadges = (p.categories || []).map(c => CATEGORIES[c]
    ? `<span class="badge badge-cat">${{escHTML(CATEGORIES[c])}}</span>` : '').join('');

  return `
  <div class="post-card" id="post-${{p.anchor}}">
    ${{mediaHTML}}
    <div class="post-body">
      <div class="post-badges">
        <span class="badge-year">${{escHTML(p.year)}}</span>
        ${{accountBadge(p.account)}}
        ${{lang}}
        ${{catBadges}}
      </div>
      <div class="post-text">${{text}}</div>
      <div class="post-date">
        ${{fmtDate(p.date)}}
      </div>
    </div>
  </div>`;
}}

function toggleSection(header) {{
  const body  = header.nextElementSibling;
  const arrow = header.querySelector('.filter-section-arrow');
  body.classList.toggle('open');
  arrow.classList.toggle('open');
}}
function toggleChip(chip) {{
  chip.classList.toggle('active');
  const section = chip.closest('.filter-section');
  const badge   = section.querySelector('.filter-section-badge');
  const n = section.querySelectorAll('.filter-chip.active').length;
  badge.textContent   = n;
  badge.style.display = n ? '' : 'none';
  applyFilters();
}}
function clearFilters() {{
  document.querySelectorAll('.filter-chip.active').forEach(c => c.classList.remove('active'));
  document.querySelectorAll('.filter-section-badge').forEach(b => {{
    b.textContent = ''; b.style.display = 'none';
  }});
  applyFilters();
}}

function applyFilters() {{
  const years    = new Set([...document.querySelectorAll('.filter-chip[data-type=year].active')].map(c => c.dataset.value));
  const accounts = new Set([...document.querySelectorAll('.filter-chip[data-type=account].active')].map(c => c.dataset.value));
  const langs    = new Set([...document.querySelectorAll('.filter-chip[data-type=lang].active')].map(c => c.dataset.value));
  const cats     = new Set([...document.querySelectorAll('.filter-chip[data-type=category].active')].map(c => c.dataset.value));

  filtered = POSTS.filter(p => {{
    if (years.size    > 0 && !years.has(p.year))        return false;
    if (accounts.size > 0 && !accounts.has(p.account))  return false;
    if (langs.size    > 0 && !langs.has(p.lang))        return false;
    if (cats.size     > 0 && !(p.categories || []).some(c => cats.has(c))) return false;
    return true;
  }});

  currentPage = 1;
  renderPage();
}}

function renderPage() {{
  const total = filtered.length;
  const pages = Math.ceil(total / PAGE_SIZE);
  const start = (currentPage - 1) * PAGE_SIZE;
  const slice = filtered.slice(start, start + PAGE_SIZE);

  document.getElementById('results-count').textContent =
    total === POSTS.length ? `${{total}} tweets` : `${{total}} de ${{POSTS.length}} tweets`;

  document.getElementById('grid').innerHTML = slice.map(postHTML).join('');

  // Paginació
  let pag = '';
  if (pages > 1) {{
    if (currentPage > 1) pag += `<button onclick="goPage(${{currentPage-1}})">&#8592; Anterior</button>`;
    pag += `<span>Pàgina ${{currentPage}} de ${{pages}}</span>`;
    if (currentPage < pages) pag += `<button onclick="goPage(${{currentPage+1}})">Següent &#8594;</button>`;
  }}
  document.getElementById('pagination').innerHTML = pag;
}}

function goPage(n) {{
  currentPage = n;
  renderPage();
  window.scrollTo(0, 0);
}}

function openLightbox(embedUrl) {{
  const lb = document.getElementById('lightbox');
  let url = embedUrl;
  // Converteix URL directa de YouTube a embed si cal
  if (url.includes('youtube.com/watch')) {{
    url = url.replace('youtube.com/watch?v=', 'www.youtube-nocookie.com/embed/');
  }} else if (url.includes('youtu.be/')) {{
    url = url.replace('youtu.be/', 'www.youtube-nocookie.com/embed/');
  }}
  document.getElementById('lightbox-iframe').src = url;
  lb.classList.add('open');
}}

function closeLightbox(e) {{
  if (!e || e.target === document.getElementById('lightbox') || e.currentTarget.tagName === 'BUTTON') {{
    document.getElementById('lightbox-iframe').src = '';
    document.getElementById('lightbox').classList.remove('open');
  }}
}}

// Deep link per anchor
filtered = POSTS.slice();
renderPage();
const hash = location.hash.replace('#','');
if (hash) {{
  setTimeout(() => {{
    const el = document.getElementById('post-' + hash);
    if (el) el.scrollIntoView({{behavior:'smooth', block:'center'}});
  }}, 200);
}}
</script>
</body>
</html>"""
    return html


# ── GENERADOR: instagram.html ─────────────────────────────────────────────────
def generate_instagram_page(posts):
    """Genera instagram.html amb grid de targetes, igual que Twitter."""
    years = get_years(posts)
    langs = get_langs(posts)

    js_posts = []
    for p in posts:
        js_posts.append({
            'anchor':     p['anchor'],
            'date':       p['date'],
            'year':       p['year'],
            'lang':       p.get('lang', ''),
            'text':       p.get('text', ''),
            'images':     p['images'],
            'categories': p.get('categories', []),
        })

    posts_json     = json.dumps(js_posts, ensure_ascii=False, separators=(',', ':'))
    year_filters   = year_filter_html(years)
    lang_filters   = lang_filter_html(langs)
    cat_filters    = category_filter_html()
    lang_labels_js = json.dumps(LANG_LABELS, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Validated ID — Instagram</title>
<style>
{COMMON_CSS}
  .post-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 1rem;
  }}
  .post-card {{
    background: #1e2a4a; border: 1px solid #2a3a5a; border-radius: 8px;
    overflow: hidden; display: flex; flex-direction: column;
    transition: transform 0.15s, border-color 0.15s; cursor: pointer;
  }}
  .post-card:hover {{ transform: translateY(-2px); border-color: #00BF71; }}
  .media-wrap {{
    position: relative; width: 100%; padding-bottom: 100%;
    background: #0d1229; overflow: hidden;
  }}
  .media-wrap img {{
    position: absolute; top: 0; left: 0;
    width: 100%; height: 100%; object-fit: cover;
    transition: opacity 0.3s;
  }}
  .media-wrap img.loading {{ opacity: 0; }}
  .post-card:hover .media-wrap img {{ opacity: 0.85; }}
  .multi-badge {{
    position: absolute; top: 8px; right: 8px;
    background: rgba(0,0,0,.65); color: #fff;
    font-size: 11px; font-weight: 600; padding: 2px 7px; border-radius: 4px;
  }}
  .post-body {{ padding: 10px 12px; display: flex; flex-direction: column; gap: 5px; flex: 1; }}
  .post-badges {{ display: flex; gap: 5px; flex-wrap: wrap; align-items: center; }}
  .badge-year {{
    background: #21262d; color: #7d8590; border: 1px solid #30363d;
    border-radius: 4px; padding: 1px 6px; font-size: 11px; font-weight: 600;
  }}
  .badge-lang {{
    background: #21262d; color: #adbac7; border: 1px solid #30363d;
    border-radius: 4px; padding: 1px 6px; font-size: 10px;
  }}
  .post-date {{ font-size: 11px; color: #6e7681; }}
  .post-text {{ font-size: 13px; color: #adbac7; line-height: 1.5; margin-top: auto; padding-top: 4px; }}
  /* Lightbox */
  .lightbox-overlay {{
    display: none; position: fixed; inset: 0; background: rgba(0,0,0,.92);
    z-index: 1000; align-items: center; justify-content: center; flex-direction: column;
    padding: 1rem;
  }}
  .lightbox-overlay.open {{ display: flex; }}
  .lightbox-overlay img {{
    max-width: 90vw; max-height: 78vh; object-fit: contain; border-radius: 4px;
  }}
  .lightbox-close {{
    position: fixed; top: 1rem; right: 1.5rem;
    background: none; border: none; color: #ccd6f6;
    font-size: 2rem; cursor: pointer; line-height: 1; z-index: 1001;
  }}
  .lightbox-close:hover {{ color: #00BF71; }}
  .lightbox-nav {{
    position: fixed; top: 50%; transform: translateY(-50%);
    background: rgba(255,255,255,.1); border: none; color: #fff;
    font-size: 2rem; cursor: pointer; padding: 0.5rem 0.8rem; border-radius: 4px;
  }}
  .lightbox-nav:hover {{ background: rgba(0,191,113,.3); }}
  .lightbox-prev {{ left: 1rem; }}
  .lightbox-next {{ right: 1rem; }}
  .lightbox-meta {{
    color: #ccd6f6; text-align: center; padding: 0.6rem 1rem;
    max-width: 600px; font-size: 13px; line-height: 1.5;
  }}
  .lightbox-counter {{ font-size: 11px; color: #8892b0; margin-top: 4px; }}
  @media (max-width: 600px) {{
    .post-grid {{ grid-template-columns: repeat(2, 1fr); }}
  }}
  @media (max-width: 350px) {{
    .post-grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

{html_header('Instagram', 'Instagram')}

<div class="layout">
  <aside class="sidebar">
    {year_filters}
    {lang_filters}
    {cat_filters}
    <button class="clear-btn" onclick="clearFilters()">Borrar filtros</button>
  </aside>

  <main>
    <div class="results-bar"><span id="count">0</span> publicaciones</div>
    <div class="post-grid" id="grid"></div>
  </main>
</div>

{html_footer()}

<!-- Lightbox -->
<div class="lightbox-overlay" id="lightbox">
  <button class="lightbox-close" onclick="closeLightbox()">&times;</button>
  <button class="lightbox-nav lightbox-prev" id="lb-prev" onclick="navImg(-1)">&#8249;</button>
  <img id="lb-img" src="" alt="">
  <button class="lightbox-nav lightbox-next" id="lb-next" onclick="navImg(1)">&#8250;</button>
  <div class="lightbox-meta">
    <div id="lb-date"></div>
    <div id="lb-caption"></div>
    <div class="lightbox-counter" id="lb-counter"></div>
  </div>
</div>

<script>
const POSTS = {posts_json};
const LANG_LABELS = {lang_labels_js};
const CATEGORIES = {json.dumps(CATEGORIES, ensure_ascii=False)};
let filtered = [...POSTS];
let lbPost = null;
let lbImgIdx = 0;

function escHTML(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}
function fmtDate(d) {{
  if (!d) return '';
  const [y, m, day] = d.split('-');
  return `${{day}}/${{m}}/${{y}}`;
}}

function toggleSection(header) {{
  const body  = header.nextElementSibling;
  const arrow = header.querySelector('.filter-section-arrow');
  body.classList.toggle('open');
  arrow.classList.toggle('open');
}}
function toggleChip(chip) {{
  chip.classList.toggle('active');
  const section = chip.closest('.filter-section');
  const badge   = section.querySelector('.filter-section-badge');
  const n = section.querySelectorAll('.filter-chip.active').length;
  badge.textContent   = n;
  badge.style.display = n ? '' : 'none';
  applyFilters();
}}
function clearFilters() {{
  document.querySelectorAll('.filter-chip.active').forEach(c => c.classList.remove('active'));
  document.querySelectorAll('.filter-section-badge').forEach(b => {{
    b.textContent = ''; b.style.display = 'none';
  }});
  applyFilters();
}}

function applyFilters() {{
  const years = new Set([...document.querySelectorAll('.filter-chip[data-type=year].active')].map(c => c.dataset.value));
  const langs = new Set([...document.querySelectorAll('.filter-chip[data-type=lang].active')].map(c => c.dataset.value));
  const cats  = new Set([...document.querySelectorAll('.filter-chip[data-type=category].active')].map(c => c.dataset.value));
  filtered = POSTS.filter(p =>
    (years.size === 0 || years.has(p.year)) &&
    (langs.size === 0 || langs.has(p.lang)) &&
    (cats.size  === 0 || (p.categories || []).some(c => cats.has(c)))
  );
  renderGrid();
}}

function renderGrid() {{
  const grid = document.getElementById('grid');
  grid.innerHTML = filtered.map((p, i) => cardHTML(p, i)).join('');
  grid.querySelectorAll('img[data-src]').forEach(img => {{
    const obs = new IntersectionObserver(entries => {{
      if (entries[0].isIntersecting) {{
        img.src = img.dataset.src;
        img.onload = () => img.classList.remove('loading');
        obs.disconnect();
      }}
    }}, {{ rootMargin: '200px' }});
    obs.observe(img);
  }});
  document.getElementById('count').textContent = filtered.length;
}}

function cardHTML(p, i) {{
  const img = p.images[0];
  const multi = p.images.length > 1 ? `<span class="multi-badge">1/${{p.images.length}}</span>` : '';
  const lang  = p.lang ? `<span class="badge-lang">${{LANG_LABELS[p.lang] || p.lang}}</span>` : '';
  const catBadges = (p.categories || []).map(c => CATEGORIES[c]
    ? `<span class="badge badge-cat">${{escHTML(CATEGORIES[c])}}</span>` : '').join('');
  const caption = p.text
    ? escHTML(p.text.substring(0, 120)) + (p.text.length > 120 ? '…' : '')
    : `<span style="color:#4a5a7a;font-style:italic">(sin texto)</span>`;
  return `<div class="post-card" id="post-${{p.anchor}}" onclick="openLightbox(${{i}}, 0)">
    <div class="media-wrap">
      <img data-src="${{escHTML(img)}}" src="" alt="" class="loading">
      ${{multi}}
    </div>
    <div class="post-body">
      <div class="post-badges">
        <span class="badge-year">${{p.year}}</span>
        ${{lang}}
        ${{catBadges}}
      </div>
      <div class="post-date">${{fmtDate(p.date)}}</div>
      <div class="post-text">${{caption}}</div>
    </div>
  </div>`;
}}

function openLightbox(filteredIdx, imgIdx) {{
  lbPost   = filtered[filteredIdx];
  lbImgIdx = imgIdx;
  showLbImage();
  document.getElementById('lightbox').classList.add('open');
  document.body.style.overflow = 'hidden';
}}

function showLbImage() {{
  document.getElementById('lb-img').src = lbPost.images[lbImgIdx];
  document.getElementById('lb-date').textContent = fmtDate(lbPost.date);
  document.getElementById('lb-caption').textContent = lbPost.text || '';
  const counter = document.getElementById('lb-counter');
  const multi = lbPost.images.length > 1;
  counter.textContent = multi ? `${{lbImgIdx + 1}} / ${{lbPost.images.length}}` : '';
  document.getElementById('lb-prev').style.display = multi ? '' : 'none';
  document.getElementById('lb-next').style.display = multi ? '' : 'none';
}}

function closeLightbox() {{
  document.getElementById('lightbox').classList.remove('open');
  document.body.style.overflow = '';
}}

function navImg(dir) {{
  lbImgIdx = (lbImgIdx + dir + lbPost.images.length) % lbPost.images.length;
  showLbImage();
}}

document.getElementById('lightbox').addEventListener('click', e => {{
  if (e.target === document.getElementById('lightbox')) closeLightbox();
}});
document.addEventListener('keydown', e => {{
  if (!document.getElementById('lightbox').classList.contains('open')) return;
  if (e.key === 'Escape') closeLightbox();
  if (e.key === 'ArrowRight') navImg(1);
  if (e.key === 'ArrowLeft') navImg(-1);
}});

renderGrid();
const hash = location.hash.replace('#', '');
if (hash) {{
  setTimeout(() => {{
    const el = document.getElementById('post-' + hash);
    if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
  }}, 200);
}}
</script>
</body>
</html>"""
    return html


# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    # Carreguem les dades de totes les xarxes disponibles
    all_posts = []
    for network in NETWORKS_AVAILABLE:
        path = f'data/{network}.json'
        if os.path.exists(path):
            posts = load_json(path)
            all_posts.extend(posts)
            print(f'✓ Carregat {path}: {len(posts)} posts')
        else:
            print(f'⚠ No trobat: {path} (executa primer parse_{network}.py)')

    if not all_posts:
        print('Cap dada disponible. Abort.')
        sys.exit(1)

    # Ordenem tots els posts de més recent a més antic
    all_posts.sort(key=date_sort_key, reverse=True)

    # Generem les pàgines per xarxa
    for network in NETWORKS_AVAILABLE:
        net_posts = [p for p in all_posts if p['network'] == network]
        if not net_posts:
            continue
        if network == 'twitter':
            filename = 'twitter.html'
            print(f'\nGenerant {filename}...')
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(generate_twitter_page(net_posts))
        elif network == 'instagram':
            filename = 'instagram.html'
            print(f'\nGenerant {filename}...')
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(generate_instagram_page(net_posts))
        else:
            filename = f'{network}.html'
            print(f'\nGenerant {filename}...')
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(generate_network_page(network, net_posts))
        size = os.path.getsize(filename) / 1024
        print(f'✓ {filename} ({size:.0f} KB, {len(net_posts)} posts)')

    print('\nGenerant imatges.html...')
    with open('imatges.html', 'w', encoding='utf-8') as f:
        f.write(generate_imatges(all_posts))
    posts_with_images = len([p for p in all_posts if p['images']])
    size = os.path.getsize('imatges.html') / 1024
    print(f'✓ imatges.html ({size:.0f} KB, {posts_with_images} posts amb imatge)')

    print('\nGenerant videos.html...')
    with open('videos.html', 'w', encoding='utf-8') as f:
        f.write(generate_videos())
    size = os.path.getsize('videos.html') / 1024
    print(f'✓ videos.html ({size:.0f} KB)')

    print('\nFet.')
