"""
parse_twitter.py
Parseja els backups dels 3 comptes de Twitter i genera data/twitter.json.

Requereix que hagin acabat:
  - archive_twitter_youtube.py  → data/videos_youtube.json (amb yt_id)
  - upload_twitter_media.py     → data/twitter_media_index.json

Filtra: exclou retweets (full_text comença per "RT @") i respostes (comença per "@")
"""

import os
import sys
import json
import re
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE     = r'C:\Users\santi\Dropbox\Social VID\Twitter'
ACCOUNTS = ['ValidatedID', 'VIDsigner', 'VIDidentity']
OUT_JSON = 'data/twitter.json'

YT_RE   = re.compile(r'(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)', re.I)
TCO_RE  = re.compile(r'https?://t\.co/\S+')
CTRL_RE = re.compile(r'[\u200b-\u200f\u202a-\u202e\u2066-\u2069]')

# ── Carrega índex de media pujada a Archive.org ───────────────────────────────
media_index = {}
if os.path.exists('data/twitter_media_index.json'):
    with open('data/twitter_media_index.json', encoding='utf-8') as f:
        media_index = json.load(f)
    print(f'✓ Carregat twitter_media_index.json: {len(media_index)} fitxers')
else:
    print('⚠ twitter_media_index.json no trobat — les URLs de media quedaran buides')

# ── Carrega videos_youtube.json per mapear yt_id → archive ───────────────────
yt_by_id = {}
if os.path.exists('data/videos_youtube.json'):
    yt_videos = json.load(open('data/videos_youtube.json', encoding='utf-8'))
    for v in yt_videos:
        if v.get('yt_id'):
            yt_by_id[v['yt_id']] = v
    print(f'✓ Carregat videos_youtube.json: {len(yt_by_id)} vídeos amb yt_id')
else:
    print('⚠ videos_youtube.json no trobat')

# ── Importa detecció d'idioma ─────────────────────────────────────────────────
from lang_detect import detect_lang
from tg_notify import notify


# ── Helpers ───────────────────────────────────────────────────────────────────
def parse_date(d):
    """Converteix data de Twitter a datetime."""
    try:
        return datetime.strptime(d, '%a %b %d %H:%M:%S +0000 %Y')
    except Exception:
        return None

def clean_text(text):
    """Neteja el text del tweet per mostrar."""
    text = CTRL_RE.sub('', text)
    text = TCO_RE.sub('', text)
    # Elimina mencions @[id:name] de Facebook que s'hagin colat
    text = re.sub(r'@\[\d+:\d+:[^\]]+\]', '', text)
    return text.strip()

def get_tweet_url(account, tweet_id):
    return f'https://x.com/{account}/status/{tweet_id}'

def get_media_url(filename):
    """Retorna la URL d'Archive.org per a un fitxer de media, o None si no existeix."""
    entry = media_index.get(filename)
    if entry:
        return entry.get('archive_url')
    return None

def get_thumb_url(filename):
    entry = media_index.get(filename)
    if entry:
        return entry.get('thumb_url')
    return None

def resolve_images(tweet_id, entities, ext_entities):
    """Retorna la llista d'imatges arxivades per a un tweet."""
    images = []
    media_dir_prefix = f'{tweet_id}-'
    for key in media_index:
        if key.startswith(media_dir_prefix) and not key.endswith('.mp4') and not key.endswith('.mp4.jpg'):
            url = get_media_url(key)
            if url:
                images.append({'url': url, 'alt': ''})
    # Ordena per nom de fitxer per consistència
    images.sort(key=lambda x: x['url'])
    return images

def resolve_video(tweet_id, entities, ext_entities):
    """Retorna el dict de vídeo natiu arxivat, o None."""
    media_dir_prefix = f'{tweet_id}-'
    for key in media_index:
        if key.startswith(media_dir_prefix) and key.endswith('.mp4'):
            archive_url = get_media_url(key)
            thumb_url   = get_thumb_url(key)
            if archive_url:
                return {
                    'embed_url':     archive_url,
                    'thumbnail_url': thumb_url or archive_url,
                    'title':         '',
                    'source':        'twitter_native',
                }
    return None

def resolve_youtube(text, entities):
    """Retorna el dict de vídeo YouTube arxivat, o None."""
    # Busca a les URLs expandides
    for u in entities.get('urls', []):
        m = YT_RE.search(u.get('expanded_url', ''))
        if m:
            yt_id = m.group(1)
            archived = yt_by_id.get(yt_id)
            if archived:
                return {
                    'embed_url':     archived['embed_url'],
                    'thumbnail_url': archived['thumbnail_url'],
                    'title':         archived.get('title', ''),
                    'source':        'youtube',
                    'yt_id':         yt_id,
                }
            else:
                # Vídeo de YouTube no arxivat (eliminat o pendent)
                thumb = f'https://img.youtube.com/vi/{yt_id}/hqdefault.jpg'
                return {
                    'embed_url':     f'https://www.youtube.com/watch?v={yt_id}',
                    'thumbnail_url': thumb,
                    'title':         '',
                    'source':        'youtube_external',
                    'yt_id':         yt_id,
                }
    return None


# ── Parseja cada compte ────────────────────────────────────────────────────────
all_posts = []

for account in ACCOUNTS:
    tweets_path = os.path.join(BASE, account, 'data', 'tweets.js')
    with open(tweets_path, encoding='utf-8') as f:
        raw = f.read()
    tweets_raw = json.loads(raw.split('= ', 1)[1])

    originals = [t['tweet'] for t in tweets_raw
                 if not t['tweet']['full_text'].startswith('RT @')
                 and not t['tweet']['full_text'].startswith('@')]

    print(f'\n@{account}: {len(tweets_raw)} total → {len(originals)} originals')

    for tw in originals:
        tweet_id  = tw['id_str']
        raw_text  = tw['full_text']
        text      = clean_text(raw_text)
        dt        = parse_date(tw['created_at'])
        entities  = tw.get('entities', {})
        ext_ent   = tw.get('extended_entities', {})

        if not dt:
            continue

        date_str = dt.strftime('%Y-%m-%d')
        year_str = dt.strftime('%Y')

        # Resolució de media
        images  = resolve_images(tweet_id, entities, ext_ent)
        video   = resolve_video(tweet_id, entities, ext_ent)
        yt_vid  = None if video else resolve_youtube(raw_text, entities)

        # Tipus de contingut
        if video:
            content_type = 'video'
        elif yt_vid:
            content_type = 'youtube'
        elif images:
            content_type = 'photo'
        else:
            content_type = 'text'

        post = {
            'id':           tweet_id,
            'anchor':       tweet_id,
            'network':      'twitter',
            'account':      account,
            'date':         date_str,
            'year':         year_str,
            'text':         text,
            'lang':         detect_lang(text),
            'images':       images,
            'video':        video or yt_vid,
            'url':          get_tweet_url(account, tweet_id),
            'content_type': content_type,
        }
        all_posts.append(post)

    # Estadístiques
    acc_posts = [p for p in all_posts if p['account'] == account]
    photos = sum(1 for p in acc_posts if p['content_type'] == 'photo')
    videos = sum(1 for p in acc_posts if p['content_type'] == 'video')
    yt     = sum(1 for p in acc_posts if p['content_type'] == 'youtube')
    texts  = sum(1 for p in acc_posts if p['content_type'] == 'text')
    print(f'  foto:{photos}  video:{videos}  youtube:{yt}  text:{texts}')

# Ordena de més recent a més antic
all_posts.sort(key=lambda p: p['date'], reverse=True)

# Guarda
with open(OUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(all_posts, f, ensure_ascii=False, indent=2)

print(f'\n✓ Generat: {OUT_JSON}')
print(f'  Posts totals: {len(all_posts)}')
notify(f'PAS 3/4 completat! twitter.json generat\nPosts: {len(all_posts)}')
from collections import Counter
langs = Counter(p['lang'] for p in all_posts)
for lang, n in sorted(langs.items(), key=lambda x: -x[1]):
    label = lang if lang else '(buit)'
    print(f'  {label}: {n}')
