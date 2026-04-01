"""
generate_fb_thumbs.py
Genera miniatures JPG dels vídeos de Facebook amb ffmpeg
i les puja a l'ítem validatedid-facebook-media d'Archive.org.

Format de miniatura: {filename}.jpg  (ex: 2119613878502630.mp4.jpg)
URL resultant: https://archive.org/download/validatedid-facebook-media/2119613878502630.mp4.jpg
"""

import os
import sys
import json
import subprocess
import tempfile

sys.stdout.reconfigure(encoding='utf-8')

FB_BASE     = r'C:\Users\santi\Dropbox\Social VID\Facebook\facebook-validatedid-01_02_2026-YinQikqt'
VIDEOS_JSON = 'data/videos_facebook.json'
ITEM_ID     = 'validatedid-facebook-media'
THUMB_DIR   = r'C:\Users\santi\Dropbox\Social VID\Facebook\thumbs_mp4'

# Comprova que existeix el directori de sortida
os.makedirs(THUMB_DIR, exist_ok=True)


def find_mp4(filename):
    """Cerca el fitxer MP4 dins del backup de Facebook."""
    for root, dirs, files in os.walk(FB_BASE):
        if filename in files:
            return os.path.join(root, filename)
    return None


def generate_thumb(mp4_path, thumb_path, time_sec=1):
    """Extreu un fotograma del vídeo amb ffmpeg."""
    cmd = [
        'ffmpeg', '-y',
        '-ss', str(time_sec),
        '-i', mp4_path,
        '-vframes', '1',
        '-q:v', '3',          # qualitat JPG: 2=millor, 5=pitjor
        '-vf', 'scale=640:-1', # amplada 640px, alçada proporcional
        thumb_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Intenta al segon 0 si el vídeo és molt curt
        cmd[3] = '0'
        result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def upload_thumb(thumb_path, remote_name):
    """Puja el thumbnail a Archive.org via la API de Python."""
    import internetarchive as ia
    try:
        r = ia.upload(
            ITEM_ID,
            files={remote_name: thumb_path},
            retries=3,
        )
        # r és una llista de respostes; comprova el codi HTTP
        ok = all(resp.status_code in (200, 201) for resp in r)
        return ok, str([resp.status_code for resp in r])
    except Exception as e:
        return False, str(e)


def check_already_uploaded(remote_name):
    """Comprova si el fitxer ja existeix a Archive.org."""
    url = f'https://archive.org/download/{ITEM_ID}/{remote_name}'
    import urllib.request
    try:
        urllib.request.urlopen(url, timeout=8)
        return True
    except Exception:
        return False


def main():
    with open(VIDEOS_JSON, encoding='utf-8') as f:
        videos = json.load(f)

    print(f'Processant {len(videos)} vídeos de Facebook...')
    print(f'Directori de miniatures: {THUMB_DIR}')
    print()

    ok = 0
    skipped = 0
    errors = []

    for filename, v in videos.items():
        # Nom del thumbnail: filename + ".jpg"  (ex: 2119613878502630.mp4.jpg)
        remote_name = filename + '.jpg'
        thumb_path  = os.path.join(THUMB_DIR, remote_name)

        # 1) Comprova si ja existeix a Archive.org
        if check_already_uploaded(remote_name):
            print(f'  ✓ Ja pujat: {remote_name}')
            skipped += 1
            continue

        # 2) Cerca el MP4 local
        mp4_path = find_mp4(filename)
        if not mp4_path:
            print(f'  ✗ No trobat localment: {filename}')
            errors.append(filename)
            continue

        # 3) Genera el thumbnail si no existeix
        if not os.path.exists(thumb_path):
            print(f'  → Generant: {remote_name}...', end=' ')
            if generate_thumb(mp4_path, thumb_path):
                print('OK', end=' ')
            else:
                print('ERROR ffmpeg')
                errors.append(filename)
                continue
        else:
            print(f'  → Thumbnail existent: {remote_name}', end=' ')

        # 4) Puja a Archive.org
        print(f'→ Pujant...', end=' ')
        success, log = upload_thumb(thumb_path, remote_name)
        if success:
            print('✓')
            ok += 1
        else:
            print(f'ERROR ia: {log[:100]}')
            errors.append(filename)

    print()
    print(f'✓ Completats: {ok}')
    print(f'  Ja existien: {skipped}')
    if errors:
        print(f'  Errors ({len(errors)}): {errors}')

    # Actualitza el JSON amb les noves URLs de miniatura
    print()
    print('Actualitzant videos_facebook.json amb les noves URLs de miniatura...')
    updated = 0
    archive_base = f'https://archive.org/download/{ITEM_ID}'
    for filename, v in videos.items():
        new_thumb = f'{archive_base}/{filename}.jpg'
        if v.get('thumbnail_url') != new_thumb:
            v['thumbnail_url'] = new_thumb
            updated += 1

    with open(VIDEOS_JSON, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)
    print(f'✓ Actualitzades {updated} entrades a {VIDEOS_JSON}')


if __name__ == '__main__':
    main()
