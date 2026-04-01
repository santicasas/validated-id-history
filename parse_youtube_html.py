"""
parse_youtube_html.py
Extreu les dades de youtube.html i genera data/videos_youtube.json.

Format de sortida:
  [
    {
      "source":     "youtube",
      "archive_id": "validatedid-20161128-firmacontudniees",
      "embed_url":  "https://archive.org/embed/validatedid-20161128-firmacontudniees?ui-theme=dark",
      "thumbnail_url": "https://archive.org/services/img/validatedid-20161128-firmacontudniees",
      "title":      "firmacontudnie.es",
      "date":       "28/11/2016",
      "year":       "2016",
      "lang":       "ES"
    },
    ...
  ]
"""

import re
import json
import sys
import os
from html import unescape as html_unescape

sys.stdout.reconfigure(encoding='utf-8')

INPUT  = 'youtube.html'
OUTPUT = 'data/videos_youtube.json'

# Regex per extreure cada bloc <div class="card" ...> ... </div>
CARD_RE = re.compile(
    r'<div class="card"\s+data-year="(\d+)"\s+data-lang="([^"]+)">'
    r'.*?<iframe src="([^"]+)"'
    r'.*?<div class="card-title">([^<]*)</div>'
    r'.*?<div class="card-date">([^<]*)</div>',
    re.DOTALL
)


def unescape(text):
    """Desescapa entitats HTML."""
    return html_unescape(text)


def main():
    with open(INPUT, encoding='utf-8') as f:
        html = f.read()

    videos = []
    seen_ids = set()

    for m in CARD_RE.finditer(html):
        year     = m.group(1)
        lang     = m.group(2)
        embed_url = m.group(3)
        title    = unescape(m.group(4).strip())
        date     = m.group(5).strip()

        # Extreu l'archive_id de l'embed_url
        # format: https://archive.org/embed/ARCHIVE_ID?ui-theme=dark
        archive_id = embed_url.split('/embed/')[-1].split('?')[0]

        # Thumbnail via Archive.org services
        thumbnail_url = f'https://archive.org/services/img/{archive_id}'

        # Clau de deduplicació: archive_id + title (pot haver-hi duplicats d'iframe)
        key = (archive_id, title)
        if key in seen_ids:
            continue
        seen_ids.add(key)

        videos.append({
            'source':        'youtube',
            'archive_id':    archive_id,
            'embed_url':     embed_url,
            'thumbnail_url': thumbnail_url,
            'title':         title,
            'date':          date,
            'year':          year,
            'lang':          lang,
        })

    os.makedirs('data', exist_ok=True)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)

    print(f'✓ Generat: {OUTPUT} ({len(videos)} vídeos de YouTube)')


if __name__ == '__main__':
    main()
