"""
parse_instagram.py
Llegeix el backup d'Instaloader i genera data/instagram.json
amb l'esquema comú del projecte.
"""

import json
import os
import glob
import lzma
import re
from datetime import datetime, timezone

# ── CONFIGURACIÓ ──────────────────────────────────────────────────────────────
BACKUP_DIR   = r'C:\Users\santi\Dropbox\Social VID\Instagram\instagram_validatedid\validatedid'
ARCHIVE_BASE = 'https://archive.org/download/validatedid-instagram-media'
OUTPUT_FILE  = 'data/instagram.json'

# ── PARSER PRINCIPAL ──────────────────────────────────────────────────────────
def parse_posts():
    # Fitxers XZ amb data (posts individuals)
    xz_files = sorted(glob.glob(os.path.join(BACKUP_DIR, '2*.json.xz')))

    posts = []
    stats = {
        'total': 0,
        'images': 0,
        'sidecars': 0,
        'videos': 0,
        'no_caption': 0,
    }

    for xf in xz_files:
        basename = os.path.basename(xf).replace('.json.xz', '')

        with lzma.open(xf) as f:
            data = json.load(f)
        node = data.get('node', {})

        stats['total'] += 1

        # ── DATA ──────────────────────────────────────────────────────────────
        ts = node.get('taken_at_timestamp')
        date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%d') if ts else basename[:10]

        # ── CAPTION ───────────────────────────────────────────────────────────
        caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
        caption = caption_edges[0]['node']['text'] if caption_edges else ''

        # Fallback: fitxer .txt
        if not caption:
            txt_path = os.path.join(BACKUP_DIR, f'{basename}.txt')
            if os.path.exists(txt_path):
                with open(txt_path, encoding='utf-8', errors='replace') as ft:
                    caption = ft.read().strip()

        if not caption:
            stats['no_caption'] += 1

        # ── IMATGES ───────────────────────────────────────────────────────────
        typename = node.get('__typename', 'GraphImage')
        images = []

        if typename == 'GraphSidecar':
            stats['sidecars'] += 1
            # Imatges numerades: basename_1.jpg, basename_2.jpg, ...
            children = node.get('edge_sidecar_to_children', {}).get('edges', [])
            for i in range(1, len(children) + 1):
                fname = f'{basename}_{i}.jpg'
                local = os.path.join(BACKUP_DIR, fname)
                if os.path.exists(local):
                    images.append(f'{ARCHIVE_BASE}/{fname}')
        elif typename == 'GraphVideo':
            stats['videos'] += 1
            # El vídeo en si (.mp4) i la miniatura (.jpg)
            mp4_name = f'{basename}.mp4'
            jpg_name = f'{basename}.jpg'
            if os.path.exists(os.path.join(BACKUP_DIR, mp4_name)):
                images.append(f'{ARCHIVE_BASE}/{jpg_name}')  # thumbnail
        else:
            stats['images'] += 1
            fname = f'{basename}.jpg'
            if os.path.exists(os.path.join(BACKUP_DIR, fname)):
                images.append(f'{ARCHIVE_BASE}/{fname}')

        # ── ID I ANCHOR ───────────────────────────────────────────────────────
        post_id = node.get('id', basename)
        shortcode = node.get('shortcode', '')
        anchor_id = f'ig-{post_id}'

        # ── URL ORIGINAL ──────────────────────────────────────────────────────
        url = f'https://www.instagram.com/p/{shortcode}/' if shortcode else None

        # ── POST FINAL ────────────────────────────────────────────────────────
        posts.append({
            'id':           post_id,
            'anchor':       anchor_id,
            'network':      'instagram',
            'date':         date_str,
            'year':         date_str[:4],
            'text':         caption,
            'images':       images,
            'video':        None,
            'url':          url,
            'page_ref':     f'instagram.html#{anchor_id}',
            'content_type': typename.replace('Graph', '').lower(),
        })

    # Ordenem per data ascendent
    posts.sort(key=lambda p: p['date'])
    return posts, stats


# ── EXECUCIÓ ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print('Parsejant posts d\'Instagram...')
    posts, stats = parse_posts()

    os.makedirs('data', exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print(f'\n✓ Generat: {OUTPUT_FILE}')
    print(f'\n── Estadístiques ──────────────────────────────')
    print(f'  Total posts:    {stats["total"]}')
    print(f'  Imatges simples:{stats["images"]}')
    print(f'  Sidecars:       {stats["sidecars"]}')
    print(f'  Vídeos:         {stats["videos"]}')
    print(f'  Sense caption:  {stats["no_caption"]}')

    print(f'\n── Primers 3 posts ────────────────────────────')
    for p in posts[:3]:
        print(f'  {p["date"]} | imgs:{len(p["images"])} | {p["text"][:60]}')

    print(f'\n── Últims 3 posts ─────────────────────────────')
    for p in posts[-3:]:
        print(f'  {p["date"]} | imgs:{len(p["images"])} | {p["text"][:60]}')

    print(f'\n── Rang de dates ──────────────────────────────')
    print(f'  {posts[0]["date"]} → {posts[-1]["date"]}')
