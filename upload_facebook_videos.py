"""
upload_facebook_videos.py
Puja els vídeos MP4 de Facebook a Archive.org i genera data/videos_facebook.json.

Col·lecció: validatedid-facebook-media
Format de data/videos_facebook.json:
  {
    "fb_filename": {
      "archive_id":    "validatedid-facebook-media",
      "embed_url":     "https://archive.org/embed/validatedid-facebook-media?start=FILENAME",
      "thumbnail_url": "https://archive.org/download/validatedid-facebook-media/FILENAME.thumbs/...",
      "title":         "...",
      "filename":      "FILENAME.mp4"
    }
  }
"""

import os
import sys
import subprocess
import glob
import json
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

IA_EXE    = r'C:\Users\santi\AppData\Local\Python\pythoncore-3.14-64\Scripts\ia.exe'
FB_BASE   = r'C:\Users\santi\Dropbox\Social VID\Facebook\facebook-validatedid-01_02_2026-YinQikqt'
ITEM_ID   = 'validatedid-facebook-media'
OUTPUT    = 'data/videos_facebook.json'


def fix_encoding(text):
    """Corregeix l'encoding corrupte dels exports de Facebook (latin1 → utf-8)."""
    if not text:
        return ''
    try:
        return text.encode('latin1').decode('utf-8')
    except Exception:
        return text


def get_videos():
    """Extreu tots els vídeos únics dels posts de Facebook."""
    posts_file = glob.glob(os.path.join(FB_BASE, '**', 'profile_posts_1.json'), recursive=True)[0]
    with open(posts_file, encoding='utf-8') as f:
        posts = json.load(f)

    videos = {}  # filename -> {path, title, timestamp}
    for p in posts:
        ts = p.get('timestamp', 0)
        # Intentem obtenir el títol del text del post
        post_text = ''
        for d in p.get('data', []):
            if 'post' in d:
                post_text = fix_encoding(d['post'])
                break

        for att in p.get('attachments', []):
            for item in att.get('data', []):
                if 'media' not in item:
                    continue
                media = item['media']
                uri = media.get('uri', '')
                if not uri.endswith('.mp4'):
                    continue

                filename = uri.split('/')[-1]
                if filename in videos:
                    continue

                full_path = os.path.join(FB_BASE, uri.replace('/', os.sep))
                if not os.path.exists(full_path):
                    continue

                # Títol: description del media, o text del post, o filename
                title = fix_encoding(media.get('description', '') or media.get('title', '') or '')
                if not title:
                    title = post_text
                # Truncar a 120 chars
                title = title[:120].split('\n')[0].strip()

                videos[filename] = {
                    'path':      full_path,
                    'title':     title,
                    'timestamp': ts,
                }

    return videos


def get_already_uploaded():
    """Obté la llista de fitxers ja pujats a Archive.org."""
    result = subprocess.run(
        [IA_EXE, 'list', ITEM_ID],
        capture_output=True, text=True, encoding='utf-8'
    )
    return set(result.stdout.splitlines())


def main():
    videos = get_videos()
    print(f'Vídeos de Facebook trobats: {len(videos)}')
    total_mb = sum(os.path.getsize(v['path']) for v in videos.values()) / 1024 / 1024
    print(f'Mida total: {total_mb:.1f} MB')
    print()

    already = get_already_uploaded()
    pending = {fn: v for fn, v in videos.items() if fn not in already}
    print(f'Ja pujats: {len(videos) - len(pending)}')
    print(f'Pendents:  {len(pending)}')
    print()

    errors = []
    for i, (filename, v) in enumerate(sorted(pending.items()), 1):
        print(f'[{i}/{len(pending)}] {filename}')
        result = subprocess.run(
            [IA_EXE, 'upload', ITEM_ID, v['path'],
             '--metadata', 'mediatype:movies',
             '--metadata', 'subject:Validated ID',
             '--metadata', 'subject:Facebook',
             '--no-derive'],
            capture_output=True, text=True, encoding='utf-8'
        )
        if result.returncode != 0:
            print(f'  ERROR: {result.stderr.strip()[:200]}')
            errors.append(filename)
        else:
            print(f'  OK')

    print()
    print(f'✓ Pujats: {len(pending) - len(errors)}')
    if errors:
        print(f'✗ Errors ({len(errors)}):')
        for e in errors:
            print(f'  {e}')

    # Genera data/videos_facebook.json
    print()
    print('Generant data/videos_facebook.json...')
    output = {}
    for filename, v in videos.items():
        output[filename] = {
            'archive_id':    ITEM_ID,
            'embed_url':     f'https://archive.org/embed/{ITEM_ID}?playlist=1&list_id={ITEM_ID}&start={filename}',
            'thumbnail_url': f'https://archive.org/download/{ITEM_ID}/{filename}.thumbs/{filename}_000001.jpg',
            'title':         v['title'],
            'filename':      filename,
            'timestamp':     v['timestamp'],
        }

    os.makedirs('data', exist_ok=True)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'✓ Generat: {OUTPUT} ({len(output)} vídeos)')


if __name__ == '__main__':
    main()
