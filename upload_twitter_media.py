"""
upload_twitter_media.py
Puja a Archive.org els fitxers de media locals dels 3 comptes de Twitter:
  - Fotos (JPG, PNG)
  - Vídeos natius (MP4, inclosos GIFs animats guardats com MP4)

Ítem destí: validatedid-twitter-media

Per als MP4 genera també una miniatura JPG amb ffmpeg.
Desa un índex JSON: data/twitter_media_index.json
  { "TWEETID-FILENAME": { "archive_url", "thumb_url", "type" }, ... }
"""

import os
import sys
import json
import subprocess
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

from tg_notify import notify

# ── Configuració ──────────────────────────────────────────────────────────────
BASE        = r'C:\Users\santi\Dropbox\Social VID\Twitter'
ACCOUNTS    = ['ValidatedID', 'VIDsigner', 'VIDidentity']
ITEM_ID     = 'validatedid-twitter-media'
THUMB_DIR   = r'C:\Users\santi\Dropbox\Social VID\Twitter\thumbs_mp4'
INDEX_JSON  = 'data/twitter_media_index.json'
IMAGE_EXTS  = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
VIDEO_EXTS  = {'.mp4'}

os.makedirs(THUMB_DIR, exist_ok=True)

# ── Carrega índex existent (per reprendre si s'interromp) ────────────────────
if os.path.exists(INDEX_JSON):
    with open(INDEX_JSON, encoding='utf-8') as f:
        index = json.load(f)
else:
    index = {}

print(f'Índex existent: {len(index)} fitxers ja processats')


# ── Helpers ───────────────────────────────────────────────────────────────────
def check_uploaded(remote_name):
    url = f'https://archive.org/download/{ITEM_ID}/{remote_name}'
    try:
        urllib.request.urlopen(url, timeout=8)
        return True
    except Exception:
        return False


def generate_thumb(mp4_path, thumb_path):
    for t in [1, 0]:
        cmd = ['ffmpeg', '-y', '-ss', str(t), '-i', mp4_path,
               '-vframes', '1', '-q:v', '3', '-vf', 'scale=640:-1', thumb_path]
        if subprocess.run(cmd, capture_output=True).returncode == 0:
            return True
    return False


IA_EXE = r'C:\Users\santi\AppData\Local\Python\pythoncore-3.14-64\Scripts\ia.exe'


def ia_upload_file(local_path, remote_name):
    cmd = [
        IA_EXE, 'upload', ITEM_ID,
        local_path,
        '-r', remote_name,
        '-R', '5',
        '-s', '10',
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        print(f'    ERROR: {(result.stdout+result.stderr).strip()[-150:]}')
    return result.returncode == 0


def save_index():
    with open(INDEX_JSON, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


# ── Recull tots els fitxers de media ─────────────────────────────────────────
all_files = []  # (account, local_path, filename)
for acc in ACCOUNTS:
    media_dir = os.path.join(BASE, acc, 'data', 'tweets_media')
    if not os.path.isdir(media_dir):
        continue
    for fname in sorted(os.listdir(media_dir)):
        ext = os.path.splitext(fname)[1].lower()
        if ext in IMAGE_EXTS or ext in VIDEO_EXTS:
            all_files.append((acc, os.path.join(media_dir, fname), fname))

photos = [(a, p, f) for a, p, f in all_files if os.path.splitext(f)[1].lower() in IMAGE_EXTS]
videos = [(a, p, f) for a, p, f in all_files if os.path.splitext(f)[1].lower() in VIDEO_EXTS]

print(f'Fotos: {len(photos)}  |  Vídeos MP4: {len(videos)}')
notify(f'PAS 2/4: Pujant media Twitter a Archive.org\nFotos: {len(photos)} | Videos: {len(videos)} | Ja indexats: {len(index)}')
print()

ok_count = 0
skip_count = 0
error_count = 0
_notify_interval = 200  # notifica cada N fotos noves

# ── Processa fotos ────────────────────────────────────────────────────────────
print(f'── Fotos ({len(photos)}) ─────────────────────────────────────────────')
for i, (acc, local_path, fname) in enumerate(photos, 1):
    key = fname
    if key in index:
        skip_count += 1
        continue

    remote_name = fname
    if check_uploaded(remote_name):
        archive_url = f'https://archive.org/download/{ITEM_ID}/{remote_name}'
        index[key] = {'archive_url': archive_url, 'thumb_url': archive_url, 'type': 'photo', 'account': acc}
        save_index()
        skip_count += 1
        print(f'  [{i}/{len(photos)}] ✓ Ja pujada: {fname}')
        continue

    print(f'  [{i}/{len(photos)}] Pujant: {fname}...', end=' ', flush=True)
    if ia_upload_file(local_path, remote_name):
        archive_url = f'https://archive.org/download/{ITEM_ID}/{remote_name}'
        index[key] = {'archive_url': archive_url, 'thumb_url': archive_url, 'type': 'photo', 'account': acc}
        save_index()
        ok_count += 1
        print('✓')
        if ok_count % _notify_interval == 0:
            notify(f'Fotos: {ok_count} pujades, {i}/{len(photos)} processades...')
    else:
        error_count += 1
        print('ERROR')

# ── Processa vídeos MP4 ───────────────────────────────────────────────────────
print()
print(f'── Vídeos MP4 ({len(videos)}) ────────────────────────────────────────')
for i, (acc, local_path, fname) in enumerate(videos, 1):
    key = fname
    thumb_name   = fname + '.jpg'
    thumb_path   = os.path.join(THUMB_DIR, thumb_name)

    if key in index:
        skip_count += 1
        continue

    # Comprova si ja existeix a Archive.org
    if check_uploaded(fname):
        archive_url = f'https://archive.org/download/{ITEM_ID}/{fname}'
        thumb_url   = f'https://archive.org/download/{ITEM_ID}/{thumb_name}' \
                      if check_uploaded(thumb_name) else archive_url
        index[key] = {'archive_url': archive_url, 'thumb_url': thumb_url, 'type': 'video', 'account': acc}
        save_index()
        skip_count += 1
        print(f'  [{i}/{len(videos)}] ✓ Ja pujat: {fname}')
        continue

    print(f'  [{i}/{len(videos)}] {fname}')

    # Genera thumbnail
    if not os.path.exists(thumb_path):
        print(f'    → Generant thumbnail...', end=' ', flush=True)
        if generate_thumb(local_path, thumb_path):
            print('OK')
        else:
            print('ERROR ffmpeg (continuem sense thumb)')
            thumb_path = None

    # Puja MP4
    print(f'    → Pujant MP4...', end=' ', flush=True)
    if not ia_upload_file(local_path, fname):
        error_count += 1
        notify(f'ERROR video Twitter: {fname}')
        print('ERROR')
        continue
    print('✓')

    # Puja thumbnail
    thumb_url = f'https://archive.org/download/{ITEM_ID}/{fname}'  # fallback
    if thumb_path and os.path.exists(thumb_path):
        print(f'    → Pujant thumbnail...', end=' ', flush=True)
        if ia_upload_file(thumb_path, thumb_name):
            thumb_url = f'https://archive.org/download/{ITEM_ID}/{thumb_name}'
            print('✓')
        else:
            print('ERROR (usant URL del MP4 com a fallback)')

    archive_url = f'https://archive.org/download/{ITEM_ID}/{fname}'
    index[key] = {'archive_url': archive_url, 'thumb_url': thumb_url, 'type': 'video', 'account': acc}
    save_index()
    ok_count += 1

# ── Resum final ───────────────────────────────────────────────────────────────
print()
print(f'── Resum ───────────────────────────────')
print(f'  Nous pujats:   {ok_count}')
print(f'  Ja existien:   {skip_count}')
print(f'  Errors:        {error_count}')
notify(f'PAS 2/4 completat!\nNous: {ok_count} | Ja existien: {skip_count} | Errors: {error_count}\nIndex total: {len(index)} fitxers')
print(f'  Índex total:   {len(index)} fitxers')
print(f'  Guardat a:     {INDEX_JSON}')
