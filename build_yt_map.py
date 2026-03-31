"""
build_yt_map.py
Construeix data/youtube_map.json:
  { youtube_id: archive_org_identifier, ... }

Llegeix els identificadors d'Archive.org de youtube.html
i els creua amb els .info.json del backup de YouTube.
"""

import re, json, os, glob, unicodedata, sys
sys.stdout.reconfigure(encoding='utf-8')

YT_BACKUP = r'C:\Users\santi\Dropbox\Social VID\Youtube\YouTubeBackup'
OUTPUT    = 'data/youtube_map.json'


def normalize(s):
    """Normalitza string per comparació de títols."""
    s = s.lower()
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    s = re.sub(r'[^a-z0-9]', '', s)
    return s


def best_match(archive_id, candidates):
    """Tria el millor candidat comparant el títol normalitzat."""
    # Saltem 'validatedid-YYYYMMDD-'
    title_part = normalize(re.sub(r'^validatedid-\d{8}-', '', archive_id))
    best, best_score = None, -1
    for c in candidates:
        # Saltem la data del nom de fitxer (primers 9 chars: YYYYMMDD + espai)
        fname = os.path.basename(c).replace('.info.json', '')
        fname_title = normalize(fname[9:] if len(fname) > 9 else fname)
        score = sum(1 for a, b in zip(title_part, fname_title) if a == b)
        if score > best_score:
            best_score = score
            best = c
    return best


def build_map():
    with open('youtube.html', encoding='utf-8') as f:
        yt_html = f.read()

    archive_ids = re.findall(r'archive\.org/embed/(validatedid-[^?"\s]+)', yt_html)

    mapping = {}
    unmatched = []

    for archive_id in archive_ids:
        m = re.match(r'validatedid-(\d{8})-', archive_id)
        if not m:
            unmatched.append(archive_id)
            continue
        date_prefix = m.group(1)

        candidates = glob.glob(os.path.join(YT_BACKUP, f'{date_prefix}*.info.json'))

        if not candidates:
            unmatched.append(archive_id)
            continue

        if len(candidates) == 1:
            chosen = candidates[0]
        else:
            chosen = best_match(archive_id, candidates)

        try:
            with open(chosen, encoding='utf-8') as f:
                info = json.load(f)
            yt_id = info.get('id', '')
            if yt_id:
                mapping[yt_id] = {
                    'archive_id':    archive_id,
                    'embed_url':     f'https://archive.org/embed/{archive_id}?ui-theme=dark',
                    'thumbnail_url': f'https://archive.org/services/img/{archive_id}',
                    'title':         info.get('title', ''),
                }
        except Exception as e:
            unmatched.append(f'{archive_id} ({e})')

    return mapping, unmatched


if __name__ == '__main__':
    mapping, unmatched = build_map()

    os.makedirs('data', exist_ok=True)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f'✓ Generat: {OUTPUT}')
    print(f'  Mapes correctes: {len(mapping)}')
    print(f'  Sense match:     {len(unmatched)}')
    if unmatched:
        for u in unmatched:
            print(f'  ✗ {u}')
