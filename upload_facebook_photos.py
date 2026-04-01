"""
upload_facebook_photos.py
Puja les fotos (JPG/PNG) de Facebook a Archive.org.

Col·lecció: validatedid-facebook-media (mateixa que els vídeos)
Reanudable: comprova quins fitxers ja estan pujats.
"""

import os
import sys
import subprocess
import glob
import json

sys.stdout.reconfigure(encoding='utf-8')

IA_EXE  = r'C:\Users\santi\AppData\Local\Python\pythoncore-3.14-64\Scripts\ia.exe'
FB_BASE = r'C:\Users\santi\Dropbox\Social VID\Facebook\facebook-validatedid-01_02_2026-YinQikqt'
ITEM_ID = 'validatedid-facebook-media'

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}


def get_photos():
    """Extreu tots els fitxers d'imatge únics dels posts de Facebook."""
    posts_file = glob.glob(os.path.join(FB_BASE, '**', 'profile_posts_1.json'), recursive=True)[0]
    with open(posts_file, encoding='utf-8') as f:
        posts = json.load(f)

    photos = {}  # filename -> full_path
    for p in posts:
        for att in p.get('attachments', []):
            for item in att.get('data', []):
                media = item.get('media', {})
                uri = media.get('uri', '')
                if not uri:
                    continue
                ext = os.path.splitext(uri)[1].lower()
                if ext not in IMAGE_EXTS:
                    continue

                filename = uri.split('/')[-1]
                if filename in photos:
                    continue

                full_path = os.path.join(FB_BASE, uri.replace('/', os.sep))
                if not os.path.exists(full_path):
                    print(f'  ⚠ No trobat: {full_path}')
                    continue

                photos[filename] = full_path

    return photos


def get_already_uploaded():
    """Obté la llista de fitxers ja pujats a Archive.org."""
    result = subprocess.run(
        [IA_EXE, 'list', ITEM_ID],
        capture_output=True, text=True, encoding='utf-8'
    )
    return set(result.stdout.splitlines())


def main():
    photos = get_photos()
    print(f'Fotos de Facebook trobades: {len(photos)}')
    total_mb = sum(os.path.getsize(p) for p in photos.values()) / 1024 / 1024
    print(f'Mida total: {total_mb:.1f} MB')
    print()

    already = get_already_uploaded()
    pending = {fn: p for fn, p in photos.items() if fn not in already}
    print(f'Ja pujades: {len(photos) - len(pending)}')
    print(f'Pendents:   {len(pending)}')
    print()

    if not pending:
        print('Res a pujar.')
        return

    errors = []
    for i, (filename, path) in enumerate(sorted(pending.items()), 1):
        size_kb = os.path.getsize(path) / 1024
        print(f'[{i}/{len(pending)}] {filename} ({size_kb:.0f} KB)')
        result = subprocess.run(
            [IA_EXE, 'upload', ITEM_ID, path,
             '--metadata', 'mediatype:image',
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
    print(f'✓ Pujades: {len(pending) - len(errors)}')
    if errors:
        print(f'✗ Errors ({len(errors)}):')
        for e in errors:
            print(f'  {e}')


if __name__ == '__main__':
    main()
