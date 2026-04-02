"""
archive_twitter_youtube.py
Descarrega els 31 vídeos de YouTube referenciats als tweets de Twitter
que encara no estan arxivats i els puja a Archive.org.

  - Canal propi (Validated ID | Signaturit Group) → validatedid-youtube-channel
  - Externs                                        → externs-youtube-channel

Actualitza data/videos_youtube.json amb les noves entrades.
"""

import os
import sys
import json
import re
import subprocess
import tempfile
import urllib.request
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

from tg_notify import notify

# ── Configuració ──────────────────────────────────────────────────────────────
DOWNLOAD_DIR   = r'C:\Users\santi\Dropbox\Social VID\Twitter\yt_downloads'
VIDEOS_YT_JSON = 'data/videos_youtube.json'

OWN_ITEM      = 'validatedid-youtube-channel'
EXTERN_ITEM   = 'externs-youtube-channel'

OWN_AUTHORS = {'validated id | signaturit group', 'validated id', 'vidsigner', 'vididentity'}

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ── Carrega les classificacions ────────────────────────────────────────────────
with open('data/twitter_yt_classify.json', encoding='utf-8') as f:
    classify = json.load(f)

all31 = classify['own'] + classify['external']

def target_item(author):
    return OWN_ITEM if author.lower().strip() in OWN_AUTHORS else EXTERN_ITEM


# ── Carrega videos_youtube.json existent ──────────────────────────────────────
with open(VIDEOS_YT_JSON, encoding='utf-8') as f:
    videos_yt = json.load(f)

existing_archive_ids = {v['archive_id'] for v in videos_yt}


# ── Helpers ───────────────────────────────────────────────────────────────────
def slugify(text):
    text = text.lower()
    text = re.sub(r'[àáâãäå]', 'a', text)
    text = re.sub(r'[èéêë]',   'e', text)
    text = re.sub(r'[ìíîï]',   'i', text)
    text = re.sub(r'[òóôõö]',  'o', text)
    text = re.sub(r'[ùúûü]',   'u', text)
    text = re.sub(r'[ñ]',      'n', text)
    text = re.sub(r'[ç]',      'c', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')[:60]


def make_archive_id(date_str, title, item):
    """Genera un archive_id consistent amb el format existent."""
    try:
        dt = datetime.strptime(date_str, '%a %b %d %H:%M:%S +0000 %Y')
        date_part = dt.strftime('%Y%m%d')
    except Exception:
        date_part = 'unknown'
    prefix = 'validatedid' if item == OWN_ITEM else 'extern'
    return f'{prefix}-{date_part}-{slugify(title)}'


IA_EXE = r'C:\Users\santi\AppData\Local\Python\pythoncore-3.14-64\Scripts\ia.exe'


def ia_upload(filepath, archive_id, title, description, date_str):
    """Puja un fitxer a Archive.org via ia.exe (suporta fitxers grans amb reintents)."""
    try:
        dt = datetime.strptime(date_str, '%a %b %d %H:%M:%S +0000 %Y')
        date_iso = dt.strftime('%Y-%m-%d')
    except Exception:
        date_iso = '2020-01-01'

    cmd = [
        IA_EXE, 'upload', archive_id,
        filepath,
        '-m', f'title:{title}',
        '-m', f'date:{date_iso}',
        '-m', 'subject:Validated ID',
        '-m', 'mediatype:movies',
        '-m', 'collection:opensource_movies',
        '-R', '5',
        '-s', '10',
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    ok = result.returncode == 0
    log = (result.stdout + result.stderr).strip()[-200:]
    return ok, log


def check_archive_exists(archive_id):
    url = f'https://archive.org/metadata/{archive_id}'
    try:
        req = urllib.request.urlopen(url, timeout=8)
        data = json.loads(req.read())
        return bool(data.get('metadata'))
    except Exception:
        return False


def get_yt_info(yt_id):
    """Obté metadades del vídeo via yt-dlp (sense descarregar)."""
    url = f'https://youtu.be/{yt_id}'
    cmd = ['python', '-m', 'yt_dlp', '--dump-json', '--no-playlist', url]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if result.returncode == 0:
        return json.loads(result.stdout)
    return None


def download_video(yt_id, out_dir):
    """Descarrega el vídeo en la millor qualitat <= 1080p."""
    url = f'https://youtu.be/{yt_id}'
    out_template = os.path.join(out_dir, f'{yt_id}.%(ext)s')
    cmd = [
        'python', '-m', 'yt_dlp',
        '-f', 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
        '--merge-output-format', 'mp4',
        '-o', out_template,
        '--no-playlist',
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode == 0:
        # Cerca el fitxer descarregat
        for f in os.listdir(out_dir):
            if f.startswith(yt_id) and f.endswith('.mp4'):
                return os.path.join(out_dir, f)
    return None


# ── Processa cada vídeo ────────────────────────────────────────────────────────
print(f'Processant {len(all31)} vídeos de YouTube...')
notify(f'PAS 1/4: Arxivant {len(all31)} videos de YouTube...')
print()

new_entries = []
errors = []
skipped = []

for v in all31:
    yt_id  = v['yt_id']
    title  = v['title']
    author = v.get('author', '')
    date   = v.get('date', '')
    item   = target_item(author)

    archive_id = make_archive_id(date, title, item)

    print(f'[{item[:10]}] {title[:55]!r}')
    print(f'  yt_id={yt_id}  archive_id={archive_id}')

    # 1) Comprova si ja existeix a Archive.org
    if archive_id in existing_archive_ids or check_archive_exists(archive_id):
        print(f'  ✓ Ja existeix, saltant.')
        # Assegura que és al JSON
        if not any(vv['archive_id'] == archive_id for vv in videos_yt):
            try:
                dt = datetime.strptime(date, '%a %b %d %H:%M:%S +0000 %Y')
                date_fmt = dt.strftime('%d/%m/%Y')
                year     = dt.strftime('%Y')
            except Exception:
                date_fmt, year = '', ''
            new_entries.append({
                'source':        item,
                'archive_id':    archive_id,
                'embed_url':     f'https://archive.org/embed/{archive_id}?ui-theme=dark',
                'thumbnail_url': f'https://archive.org/services/img/{archive_id}',
                'title':         title,
                'date':          date_fmt,
                'year':          year,
                'lang':          '',
                'yt_id':         yt_id,
                'author':        author,
            })
        skipped.append(yt_id)
        print()
        continue

    # 2) Descarrega
    print(f'  → Descarregant...', end=' ', flush=True)
    mp4_path = download_video(yt_id, DOWNLOAD_DIR)
    if not mp4_path:
        print('ERROR yt-dlp')
        errors.append((yt_id, title, 'download failed'))
        notify(f'ERROR descarga: {title[:50]}\nhttps://youtu.be/{yt_id}')
        print()
        continue
    print(f'OK ({os.path.getsize(mp4_path)//1024//1024} MB)')

    # 3) Puja a Archive.org
    print(f'  → Pujant a {archive_id}...', end=' ', flush=True)
    ok, log = ia_upload(mp4_path, archive_id, title, f'Video from YouTube: https://youtu.be/{yt_id}', date)
    if ok:
        print('✓')
    else:
        print(f'ERROR: {log[:80]}')
        errors.append((yt_id, title, f'upload failed: {log}'))
        notify(f'ERROR pujada: {title[:50]}\n{log[:100]}')
        print()
        continue

    # 4) Afegeix al JSON
    try:
        dt = datetime.strptime(date, '%a %b %d %H:%M:%S +0000 %Y')
        date_fmt = dt.strftime('%d/%m/%Y')
        year     = dt.strftime('%Y')
    except Exception:
        date_fmt, year = '', ''

    new_entries.append({
        'source':        item,
        'archive_id':    archive_id,
        'embed_url':     f'https://archive.org/embed/{archive_id}?ui-theme=dark',
        'thumbnail_url': f'https://archive.org/services/img/{archive_id}',
        'title':         title,
        'date':          date_fmt,
        'year':          year,
        'lang':          '',
        'yt_id':         yt_id,
        'author':        author,
    })
    print()

# ── Afegeix idioma als nous vídeos ────────────────────────────────────────────
if new_entries:
    from lang_detect import detect_lang
    for entry in new_entries:
        if not entry.get('lang'):
            entry['lang'] = detect_lang(entry['title'])

# ── Actualitza videos_youtube.json ───────────────────────────────────────────
if new_entries:
    videos_yt.extend(new_entries)
    with open(VIDEOS_YT_JSON, 'w', encoding='utf-8') as f:
        json.dump(videos_yt, f, ensure_ascii=False, indent=2)
    print(f'✓ Afegides {len(new_entries)} entrades a {VIDEOS_YT_JSON}')
    print(f'  Total ara: {len(videos_yt)} vídeos')

# ── Resum ────────────────────────────────────────────────────────────────────
print()
print(f'── Resum ───────────────────────────────')
print(f'  Nous pujats:   {len(new_entries) - len(skipped)}')
print(f'  Ja existien:   {len(skipped)}')
print(f'  Errors:        {len(errors)}')
if errors:
    print(f'\n  Errors detall:')
    for yt_id, title, reason in errors:
        print(f'    {yt_id} | {title[:50]} | {reason}')

_nous = len(new_entries) - len(skipped)
_msg = f'PAS 1/4 completat!\nNous: {_nous} | Ja existien: {len(skipped)} | Errors: {len(errors)}'
if errors:
    _msg += '\nFallats:\n' + '\n'.join(f'  - {t[:40]}' for _, t, _ in errors)
notify(_msg)
