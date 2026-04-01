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
NETWORKS_AVAILABLE = ['linkedin', 'instagram', 'facebook']

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

  .filter-section { margin-bottom: 1.5rem; }
  .filter-title {
    font-size: 0.7rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1px;
    color: #00BF71; margin-bottom: 0.6rem;
  }
  .checkbox-label {
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.3rem 0; cursor: pointer;
    font-size: 0.88rem; color: #ccd6f6; user-select: none;
  }
  .checkbox-label:hover { color: #fff; }
  .checkbox-label input[type=checkbox] {
    accent-color: #00BF71; width: 14px; height: 14px; cursor: pointer;
  }
  .clear-btn {
    width: 100%; background: transparent;
    border: 1px solid #2a3a5a; color: #8892b0;
    padding: 0.4rem 0.8rem; border-radius: 4px;
    cursor: pointer; font-size: 0.82rem; margin-top: 0.5rem; transition: all 0.2s;
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

  footer {
    background: #0d1229; border-top: 1px solid #2a3a5a;
    text-align: center; padding: 1rem; font-size: 0.8rem; color: #8892b0;
  }
  footer a { color: #00BF71; text-decoration: none; }
"""

def html_header(subtitle, active_page):
    nav_pages = [
        ('imatges.html',   'Imágenes'),
        ('videos.html',    'Vídeos'),
        ('linkedin.html',  'LinkedIn'),
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
  Archivo personal &middot; Imágenes alojadas en <a href="https://archive.org" target="_blank">Internet Archive</a> &middot; Validated ID (2012&ndash;2026)
</footer>"""

def year_filter_html(years):
    html = ''
    for y in years:
        html += f'<label class="checkbox-label"><input type="checkbox" class="filter-cb" data-type="year" value="{y}"> {y}</label>\n'
    return html

LANG_LABELS = {
    'ES': 'ES 🇪🇸', 'EN': 'EN 🇬🇧', 'DE': 'DE 🇩🇪',
    'FR': 'FR 🇫🇷', 'CA': 'CA 🟨', 'PT': 'PT 🇵🇹',
}
LANG_ORDER = ['ES', 'EN', 'DE', 'FR', 'CA', 'PT']

def lang_filter_html(langs):
    langs_sorted = sorted(langs, key=lambda l: LANG_ORDER.index(l) if l in LANG_ORDER else 99)
    html = ''
    for l in langs_sorted:
        label = LANG_LABELS.get(l, l)
        html += f'<label class="checkbox-label"><input type="checkbox" class="filter-cb" data-type="lang" value="{esc(l)}"> {label}</label>\n'
    return html

def get_langs(posts):
    return sorted(set(p.get('lang','') for p in posts if p.get('lang','')),
                  key=lambda l: LANG_ORDER.index(l) if l in LANG_ORDER else 99)

def network_filter_html(networks):
    html = ''
    for n in networks:
        label = NETWORK_LABELS.get(n, n)
        html += f'<label class="checkbox-label"><input type="checkbox" class="filter-cb" data-type="network" value="{n}"> {label}</label>\n'
    return html


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
            'anchor':  p['anchor'],
            'date':    p['date'],
            'year':    p['year'],
            'lang':    p.get('lang', ''),
            'type':    p.get('content_type', 'none'),
            'text':    p['text'],
            'images':  p['images'],
            'video':   p.get('video'),
            'url':     p.get('url'),
            'pageRef': p['page_ref'],
        })

    posts_json = json.dumps(js_posts, ensure_ascii=False, separators=(',', ':'))

    content_type_labels_js = json.dumps(CONTENT_TYPE_LABELS, ensure_ascii=False)

    year_filters  = year_filter_html(years)
    lang_filters  = lang_filter_html(langs)

    media_filters = """<label class="checkbox-label"><input type="checkbox" class="filter-cb" data-type="media" value="images"> Con imágenes</label>
<label class="checkbox-label"><input type="checkbox" class="filter-cb" data-type="media" value="video"> Con vídeo</label>"""

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
  @media (max-width: 700px) {{
    .sidebar {{ display: none; }}
  }}
</style>
</head>
<body>

{html_header(page_title, page_name)}

<div class="layout">
  <aside class="sidebar">
    <div class="filter-section">
      <div class="filter-title">Año</div>
      {year_filters}
    </div>
    <div class="filter-section">
      <div class="filter-title">Contenido</div>
      {media_filters}
    </div>
    <div class="filter-section">
      <div class="filter-title">Idioma</div>
      {lang_filters}
    </div>
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
const PAGE_SIZE = {PAGE_SIZE};

let filtered = [...POSTS];
let currentPage = 0;
let lbImages = [];
let lbVideoUrl = null;
let lbIdx = 0;

// ── FILTRES ───────────────────────────────────────────────────────────────────
function applyFilters() {{
  const years  = new Set([...document.querySelectorAll('.filter-cb[data-type=year]:checked')].map(c => c.value));
  const media  = new Set([...document.querySelectorAll('.filter-cb[data-type=media]:checked')].map(c => c.value));
  const langs  = new Set([...document.querySelectorAll('.filter-cb[data-type=lang]:checked')].map(c => c.value));
  filtered = POSTS.filter(p => {{
    if (years.size > 0 && !years.has(p.year)) return false;
    if (media.has('images') && p.images.length === 0) return false;
    if (media.has('video')  && !p.video)              return false;
    if (langs.size > 0 && !langs.has(p.lang))         return false;
    return true;
  }});
  currentPage = 0;
  renderPage();
}}

function clearFilters() {{
  document.querySelectorAll('.filter-cb').forEach(c => c.checked = false);
  applyFilters();
}}

document.querySelectorAll('.filter-cb').forEach(cb => cb.addEventListener('change', applyFilters));

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

  return `<div class="post-card" id="${{escAttr(p.anchor)}}">
    <div class="post-header">
      <span class="badge badge-year">${{p.year}}</span>
      <span class="badge badge-type">${{typeLabel}}</span>
      <span class="post-date">${{p.date}}</span>
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
        js_posts.append({
            'anchor':   p['anchor'],
            'network':  p['network'],
            'date':     p['date'],
            'year':     p['year'],
            'lang':     p.get('lang', ''),
            'caption':  truncate(p['text'], 200),
            'images':   p['images'],
            'pageRef':  p['page_ref'],
        })

    posts_json       = json.dumps(js_posts, ensure_ascii=False, separators=(',', ':'))
    network_labels   = json.dumps(NETWORK_LABELS, ensure_ascii=False)
    network_colors   = json.dumps(NETWORK_BADGE_COLORS, ensure_ascii=False)

    year_filters    = year_filter_html(years)
    network_filters = network_filter_html(networks)
    lang_filters_im = lang_filter_html(langs)

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
    <div class="filter-section">
      <div class="filter-title">Año</div>
      {year_filters}
    </div>
    <div class="filter-section">
      <div class="filter-title">Red</div>
      {network_filters}
    </div>
    <div class="filter-section">
      <div class="filter-title">Idioma</div>
      {lang_filters_im}
    </div>
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

let filtered = [...POSTS];
let lbVisible = [];
let lbIdx = 0;

// ── FILTRES ───────────────────────────────────────────────────────────────────
function applyFilters() {{
  const years    = new Set([...document.querySelectorAll('.filter-cb[data-type=year]:checked')].map(c => c.value));
  const networks = new Set([...document.querySelectorAll('.filter-cb[data-type=network]:checked')].map(c => c.value));
  const langs    = new Set([...document.querySelectorAll('.filter-cb[data-type=lang]:checked')].map(c => c.value));
  filtered = POSTS.filter(p =>
    (years.size    === 0 || years.has(p.year)) &&
    (networks.size === 0 || networks.has(p.network)) &&
    (langs.size    === 0 || langs.has(p.lang))
  );
  renderGrid();
}}

function clearFilters() {{
  document.querySelectorAll('.filter-cb').forEach(c => c.checked = false);
  applyFilters();
}}

document.querySelectorAll('.filter-cb').forEach(cb => cb.addEventListener('change', applyFilters));

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

function cardHTML(p, i) {{
  const netColor = NETWORK_COLORS[p.network] || '#2a3a5a';
  const netLabel = NETWORK_LABELS[p.network] || p.network;
  const captionClass = p.caption ? 'card-caption' : 'card-caption empty';
  const captionText  = p.caption || '(sin texto)';
  const multiText    = p.images.length > 1 ? `<span class="multi-badge">1/${{p.images.length}}</span>` : '';

  return `<div class="card" data-idx="${{i}}">
    <div class="card-img-wrap" onclick="openLightbox(${{i}})">
      <img data-src="${{p.images[0]}}" src="" alt="" class="loading">
      ${{multiText}}
    </div>
    <div class="card-body">
      <div class="badges">
        <span class="badge badge-year">${{p.year}}</span>
        <span class="badge badge-network" style="background:${{netColor}}">${{netLabel}}</span>
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
        })
    return result


def generate_videos():
    """Genera videos.html combinant YouTube i Facebook."""
    # Carrega vídeos de YouTube
    yt_videos = []
    if os.path.exists('data/videos_youtube.json'):
        yt_videos = load_json('data/videos_youtube.json')
        for v in yt_videos:
            v.setdefault('source', 'youtube')

    # Carrega vídeos de Facebook
    fb_videos = load_facebook_videos()

    all_videos = yt_videos + fb_videos

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

    # Filtres d'any
    year_filters_html = ''
    for y in years:
        year_filters_html += f'<label class="checkbox-label"><input type="checkbox" class="filter-cb" data-type="year" value="{y}"> {y}</label>\n'

    # Filtres d'idioma — ordre per freqüència
    lang_labels = {
        'ES': 'ES 🇪🇸', 'EN': 'EN 🇬🇧', 'DE': 'DE 🇩🇪',
        'FR': 'FR 🇫🇷', 'CA': 'CAT', 'CAT': 'CAT',
    }
    lang_order = ['ES', 'EN', 'DE', 'FR', 'CA', 'CAT']
    langs_sorted = sorted(langs, key=lambda l: lang_order.index(l) if l in lang_order else 99)
    lang_filters_html = ''
    for lang in langs_sorted:
        label = lang_labels.get(lang, lang)
        lang_filters_html += f'<label class="checkbox-label"><input type="checkbox" class="filter-cb" data-type="lang" value="{esc(lang)}"> {label}</label>\n'

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
    <div class="filter-section">
      <div class="filter-title">Año</div>
      {year_filters_html}
    </div>
    <div class="filter-section">
      <div class="filter-title">Fuente</div>
      <label class="checkbox-label"><input type="checkbox" class="filter-cb" data-type="source" value="youtube"> ▶ YouTube</label>
      <label class="checkbox-label"><input type="checkbox" class="filter-cb" data-type="source" value="facebook"> 📘 Facebook</label>
    </div>
    <div class="filter-section">
      <div class="filter-title">Idioma</div>
      {lang_filters_html}
    </div>
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

let filtered = [...VIDEOS];

function applyFilters() {{
  const years   = new Set([...document.querySelectorAll('.filter-cb[data-type=year]:checked')].map(c => c.value));
  const sources = new Set([...document.querySelectorAll('.filter-cb[data-type=source]:checked')].map(c => c.value));
  const langs   = new Set([...document.querySelectorAll('.filter-cb[data-type=lang]:checked')].map(c => c.value));
  filtered = VIDEOS.filter(v => {{
    if (years.size   > 0 && !years.has(v.year))     return false;
    if (sources.size > 0 && !sources.has(v.source)) return false;
    if (langs.size   > 0 && !langs.has(v.lang))     return false;
    return true;
  }});
  renderGrid();
}}

function clearFilters() {{
  document.querySelectorAll('.filter-cb').forEach(c => c.checked = false);
  applyFilters();
}}

document.querySelectorAll('.filter-cb').forEach(cb => cb.addEventListener('change', applyFilters));

function escHTML(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}
function escAttr(s) {{
  return String(s).replace(/"/g,'&quot;');
}}

function cardHTML(v, i) {{
  const srcBadge = v.source === 'youtube'
    ? '<span class="badge badge-year badge-source-yt">YouTube</span>'
    : '<span class="badge badge-year badge-source-fb">Facebook</span>';
  const langBadge = v.lang
    ? `<span class="badge badge-lang">${{escHTML(v.lang)}}</span>`
    : '';
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
