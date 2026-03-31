import json, sys, glob, os
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

ARCHIVE_BASE = 'https://archive.org/download/validatedid-linkedin-media'
backup = r'C:\Users\santi\Dropbox\Social VID\Linkedin\backup'
post_files = sorted(glob.glob(os.path.join(backup, '02_posts_20*.json')))

items = []
for pf in post_files:
    with open(pf, encoding='utf-8') as f:
        data = json.load(f)
    for key, post in data['results'].items():
        local = post.get('localMedia', [])
        if not local:
            continue
        ts = post.get('publishedAt') or post.get('created', {}).get('time')
        date_str = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime('%Y-%m-%d') if ts else 'unknown'
        images = []
        for m in local:
            filename = m.replace('\\', '/').split('/')[-1]
            images.append(f'{ARCHIVE_BASE}/{filename}')
        items.append({
            'id': post.get('id'),
            'date': date_str,
            'year': date_str[:4] if date_str != 'unknown' else 'unknown',
            'network': 'linkedin',
            'caption': post.get('commentary', '').strip()[:200],
            'images': images
        })
    if len(items) >= 20:
        break

items = items[:20]

os.makedirs('data', exist_ok=True)
with open('data/test_linkedin.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, indent=2, ensure_ascii=False)

print(f'Generat: {len(items)} items')
for i in items[:3]:
    print(f"  {i['date']} | {i['images'][0].split('/')[-1]} | {i['caption'][:60]}")
