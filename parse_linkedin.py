"""
parse_linkedin.py
Llegeix els fitxers de backup de LinkedIn i genera data/linkedin.json
amb l'esquema comú del projecte.
"""

import json
import os
import glob
import re
from datetime import datetime, timezone
from lang_detect import detect_lang

# ── CONFIGURACIÓ ──────────────────────────────────────────────────────────────
BACKUP_DIR   = r'C:\Users\santi\Dropbox\Social VID\Linkedin\backup'
ARCHIVE_BASE = 'https://archive.org/download/validatedid-linkedin-media'
OUTPUT_FILE  = 'data/linkedin.json'
YT_MAP_FILE  = 'data/youtube_map.json'

# ── NETEJA DE TEXT ────────────────────────────────────────────────────────────
def clean_text(text):
    """Neteja el text de LinkedIn eliminant sintaxi interna."""
    if not text:
        return ''
    # Mencions: @[Empresa](urn:li:...) → Empresa
    text = re.sub(r'@\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Hashtags: {hashtag|\#|eSign} → #eSign
    text = re.sub(r'\{hashtag\|\\#\|(\w+)\}', r'#\1', text)
    # Escapes de markdown: \# → #, \* → *, etc.
    text = re.sub(r'\\([#*()\[\]_~`>])', r'\1', text)
    # Espais múltiples i línies en blanc excessives
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# ── CONVERSIÓ DE DATA ─────────────────────────────────────────────────────────
def ts_to_date(ts):
    """Converteix timestamp en ms a string YYYY-MM-DD."""
    if not ts:
        return None
    return datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime('%Y-%m-%d')

# ── PARSER PRINCIPAL ──────────────────────────────────────────────────────────
def parse_posts():
    # Carrega el mapa YouTube ID → Archive.org
    yt_map = {}
    if os.path.exists(YT_MAP_FILE):
        with open(YT_MAP_FILE, encoding='utf-8') as f:
            yt_map = json.load(f)

    post_files = sorted(glob.glob(os.path.join(BACKUP_DIR, '02_posts_20*.json')))

    posts = []
    stats = {
        'total': 0,
        'with_images': 0,
        'multi_image': 0,
        'no_image': 0,
        'no_date': 0,
        'content_types': {}
    }

    for pf in post_files:
        year_label = os.path.basename(pf).replace('02_posts_', '').replace('.json', '')
        with open(pf, encoding='utf-8') as f:
            data = json.load(f)

        results = data.get('results', {})
        for key, post in results.items():
            stats['total'] += 1

            # ── DATA ──────────────────────────────────────────────────────────
            ts = post.get('publishedAt') or post.get('created', {}).get('time')
            date_str = ts_to_date(ts)
            if not date_str:
                stats['no_date'] += 1
                date_str = f'{year_label}-01-01'  # fallback a l'any del fitxer

            # ── IMATGES I VÍDEOS NATIUS ───────────────────────────────────────
            local_media = post.get('localMedia', [])
            images = []
            native_video_filename = None
            for m in local_media:
                filename = m.replace('\\', '/').split('/')[-1]
                if filename.endswith('_video.mp4'):
                    native_video_filename = filename
                else:
                    images.append(f'{ARCHIVE_BASE}/{filename}')

            if len(images) == 0 and not native_video_filename:
                stats['no_image'] += 1
            elif len(images) == 1:
                stats['with_images'] += 1
            elif len(images) > 1:
                stats['multi_image'] += 1

            # ── TIPUS DE CONTINGUT ────────────────────────────────────────────
            content = post.get('content', {})
            content_type = list(content.keys())[0] if content else 'none'
            stats['content_types'][content_type] = stats['content_types'].get(content_type, 0) + 1

            # ── ID NET ────────────────────────────────────────────────────────
            post_id = post.get('id', key)
            anchor_id = post_id.replace(':', '-').replace('urn-li-share-', '')

            # ── VÍDEO NATIU DE LINKEDIN → ARCHIVE.ORG ─────────────────────────
            video = None
            if native_video_filename:
                fn = native_video_filename
                fn_no_ext = fn.replace('.mp4', '')
                video = {
                    'embed_url':     f'{ARCHIVE_BASE}/{fn}?ui-theme=dark'.replace('/download/', '/embed/'),
                    'thumbnail_url': f'{ARCHIVE_BASE}/validatedid-linkedin-media.thumbs/{fn_no_ext}_000001.jpg',
                    'title':         clean_text(post.get('commentary', ''))[:120],
                }
                stats['content_types']['native_video'] = stats['content_types'].get('native_video', 0) + 1

            # ── VÍDEO DE YOUTUBE → ARCHIVE.ORG ────────────────────────────────
            if not video:
                content = post.get('content', {})
                article = content.get('article', {})
                article_source = article.get('source', '') or ''
                yt_match = re.search(r'(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})', article_source)
                if yt_match:
                    yt_id = yt_match.group(1)
                    if yt_id in yt_map:
                        video = yt_map[yt_id]

            # ── POST FINAL ────────────────────────────────────────────────────
            posts.append({
                'id':           post_id,
                'anchor':       anchor_id,
                'network':      'linkedin',
                'date':         date_str,
                'year':         date_str[:4],
                'text':         clean_text(post.get('commentary', '')),
                'lang':         detect_lang(clean_text(post.get('commentary', ''))),
                'images':       images,
                'video':        video,  # None o {archive_id, embed_url, thumbnail_url, title}
                'url':          None,
                'page_ref':     f'linkedin.html#{anchor_id}',
                'content_type': content_type
            })

    # Ordenem per data ascendent
    posts.sort(key=lambda p: p['date'])

    return posts, stats


# ── EXECUCIÓ ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print('Parsejant posts de LinkedIn...')
    posts, stats = parse_posts()

    os.makedirs('data', exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print(f'\n✓ Generat: {OUTPUT_FILE}')
    print(f'\n── Estadístiques ──────────────────────────────')
    native_vids = len([p for p in posts if p.get('video') and 'embed/validatedid-linkedin-media' in (p['video'].get('embed_url') or '')])
    print(f'  Total posts:           {stats["total"]}')
    print(f'  Amb 1 imatge:          {stats["with_images"]}')
    print(f'  Amb múltiples imatges: {stats["multi_image"]}')
    print(f'  Vídeos natius:         {native_vids}')
    print(f'  Sense imatge:          {stats["no_image"]}')
    print(f'  Sense data:            {stats["no_date"]}')
    print(f'\n── Tipus de contingut ─────────────────────────')
    for ct, n in sorted(stats['content_types'].items(), key=lambda x: -x[1]):
        print(f'  {ct:<20} {n}')

    # Mostra els 3 primers i 3 últims per validar
    print(f'\n── Primers 3 posts ────────────────────────────')
    for p in posts[:3]:
        print(f'  {p["date"]} | {p["content_type"]:<12} | imgs:{len(p["images"])} | {p["text"][:60]}')

    print(f'\n── Últims 3 posts ─────────────────────────────')
    for p in posts[-3:]:
        print(f'  {p["date"]} | {p["content_type"]:<12} | imgs:{len(p["images"])} | {p["text"][:60]}')

    # Valida alguns casos especials
    print(f'\n── Validació ──────────────────────────────────')
    multi = [p for p in posts if len(p['images']) > 1]
    print(f'  Post amb més imatges: {max(len(p["images"]) for p in posts)} imatges')
    print(f'  Exemple multi-imatge: {multi[0]["date"]} | {multi[0]["text"][:50]}')
    no_text = [p for p in posts if not p['text']]
    print(f'  Posts sense text:     {len(no_text)}')
    print(f'  Rang de dates:        {posts[0]["date"]} → {posts[-1]["date"]}')
