"""
parse_facebook.py
Genera data/facebook.json a partir del backup de Facebook.

Esquema de sortida (comú a totes les xarxes):
  {
    "id":           "fb-1747206798",
    "anchor":       "fb-1747206798",
    "network":      "facebook",
    "date":         "14/05/2025",
    "year":         "2025",
    "text":         "...",
    "images":       ["https://archive.org/download/..."],
    "video":        { "embed_url": "...", "thumbnail_url": "...", "title": "..." } | null,
    "url":          null,
    "page_ref":     "facebook.html#fb-1747206798",
    "content_type": "photo" | "multiPhoto" | "video" | "none"
  }
"""

import os
import sys
import json
import glob
import re
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

FB_BASE     = r'C:\Users\santi\Dropbox\Social VID\Facebook\facebook-validatedid-01_02_2026-YinQikqt'
ITEM_ID     = 'validatedid-facebook-media'
ARCHIVE_URL = f'https://archive.org/download/{ITEM_ID}'
VIDEOS_JSON = 'data/videos_facebook.json'
OUTPUT      = 'data/facebook.json'

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}


# ── UTILITATS ─────────────────────────────────────────────────────────────────

def fix_encoding(text):
    """Corregeix l'encoding corrupte dels exports de Facebook (latin1 → utf-8)."""
    if not text:
        return ''
    try:
        return text.encode('latin1').decode('utf-8')
    except Exception:
        return text


def clean_mentions(text):
    """Converteix @[id:size:Nom] → Nom."""
    return re.sub(r'@\[\d+:\d+:([^\]]+)\]', r'\1', text)


def clean_text(text):
    """Neteja el text d'un post de Facebook."""
    if not text:
        return ''
    text = fix_encoding(text)
    text = clean_mentions(text)
    return text.strip()


def ts_to_date(ts):
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime('%d/%m/%Y'), dt.strftime('%Y')


def image_url(filename):
    return f'{ARCHIVE_URL}/{filename}'


# ── PARSER ────────────────────────────────────────────────────────────────────

def parse_posts():
    posts_file = glob.glob(os.path.join(FB_BASE, '**', 'profile_posts_1.json'), recursive=True)[0]
    with open(posts_file, encoding='utf-8') as f:
        raw_posts = json.load(f)

    # Carrega el mapa de vídeos per filename
    videos_map = {}
    if os.path.exists(VIDEOS_JSON):
        vid_data = json.load(open(VIDEOS_JSON, encoding='utf-8'))
        for filename, v in vid_data.items():
            videos_map[filename] = v

    # Mapa per evitar duplicats de timestamp (en cas de múltiples posts al mateix segon)
    seen_anchors = {}

    posts = []
    for p in raw_posts:
        ts = p.get('timestamp', 0)
        date_str, year_str = ts_to_date(ts)

        # Anchor únic per timestamp
        base_anchor = f'fb-{ts}'
        if base_anchor in seen_anchors:
            seen_anchors[base_anchor] += 1
            anchor = f'{base_anchor}-{seen_anchors[base_anchor]}'
        else:
            seen_anchors[base_anchor] = 0
            anchor = base_anchor

        # Text principal del post
        post_text = ''
        for d in p.get('data', []):
            if 'post' in d:
                post_text = clean_text(d['post'])
                break

        # Recull les imatges i vídeos dels adjunts
        images = []
        video = None

        for att in p.get('attachments', []):
            for item in att.get('data', []):
                media = item.get('media', {})
                uri = media.get('uri', '')
                if not uri:
                    continue

                filename = uri.split('/')[-1]
                ext = os.path.splitext(filename)[1].lower()

                if ext in IMAGE_EXTS:
                    # Comprova que el fitxer existeix al backup local
                    full_path = os.path.join(FB_BASE, uri.replace('/', os.sep))
                    if os.path.exists(full_path):
                        images.append(image_url(filename))
                    # Si no existeix localment, no l'afegim (no estarà a Archive.org)

                elif ext == '.mp4':
                    # Busca la informació del vídeo al mapa precalculat
                    if filename in videos_map:
                        v = videos_map[filename]
                        # Intentem obtenir el títol del vídeo: media description o text del post
                        title = clean_text(media.get('description', '') or media.get('title', ''))
                        if not title:
                            title = post_text[:80] if post_text else filename
                        video = {
                            'embed_url':     v['embed_url'],
                            'thumbnail_url': v['thumbnail_url'],
                            'title':         title,
                        }

        # Si el post no té text, intentem agafar la descripció de la primera imatge
        if not post_text:
            for att in p.get('attachments', []):
                for item in att.get('data', []):
                    media = item.get('media', {})
                    desc = clean_text(media.get('description', '') or media.get('title', ''))
                    if desc:
                        post_text = desc
                        break
                if post_text:
                    break

        # Determina el content_type
        if video:
            content_type = 'video'
        elif len(images) > 1:
            content_type = 'multiPhoto'
        elif len(images) == 1:
            content_type = 'photo'
        else:
            content_type = 'none'

        # Salta els posts completament buits (sense text, imatges ni vídeo)
        if not post_text and not images and not video:
            continue

        posts.append({
            'id':           anchor,
            'anchor':       anchor,
            'network':      'facebook',
            'date':         date_str,
            'year':         year_str,
            'text':         post_text,
            'images':       images,
            'video':        video,
            'url':          None,
            'page_ref':     f'facebook.html#{anchor}',
            'content_type': content_type,
        })

    return posts


def main():
    print('Parsejant posts de Facebook...')
    posts = parse_posts()

    # Ordena per data descendent (més recent primer) — com els vídeos
    posts.sort(key=lambda p: p['date'][6:] + p['date'][3:5] + p['date'][:2], reverse=True)

    os.makedirs('data', exist_ok=True)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    n_images = sum(len(p['images']) for p in posts)
    n_video  = sum(1 for p in posts if p['video'])
    n_text   = sum(1 for p in posts if p['content_type'] == 'none')

    print(f'✓ Generat: {OUTPUT}')
    print(f'  Posts totals:   {len(posts)}')
    print(f'  Amb imatges:    {sum(1 for p in posts if p["images"])} ({n_images} imatges)')
    print(f'  Amb vídeo:      {n_video}')
    print(f'  Només text:     {n_text}')


if __name__ == '__main__':
    main()
