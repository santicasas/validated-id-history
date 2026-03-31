"""
upload_instagram.py
Puja totes les imatges i vídeos d'Instagram a Archive.org.
Col·lecció: validatedid-instagram-media
"""

import os
import sys
import subprocess
import glob

sys.stdout.reconfigure(encoding='utf-8')

IA_EXE    = r'C:\Users\santi\AppData\Local\Python\pythoncore-3.14-64\Scripts\ia.exe'
BACKUP    = r'C:\Users\santi\Dropbox\Social VID\Instagram\instagram_validatedid\validatedid'
ITEM_ID   = 'validatedid-instagram-media'

def get_already_uploaded():
    """Obté la llista de fitxers ja pujats a Archive.org."""
    result = subprocess.run(
        [IA_EXE, 'list', ITEM_ID],
        capture_output=True, text=True, encoding='utf-8'
    )
    return set(result.stdout.splitlines())

def main():
    # Media a pujar: JPGs i MP4s amb data, excloent profile pics
    media = sorted(
        glob.glob(os.path.join(BACKUP, '2*.jpg')) +
        glob.glob(os.path.join(BACKUP, '2*.mp4'))
    )
    media = [f for f in media if 'profile_pic' not in f]

    print(f'Total fitxers a pujar: {len(media)}')
    total_mb = sum(os.path.getsize(f) for f in media) / 1024 / 1024
    print(f'Mida total: {total_mb:.1f} MB')
    print()

    already = get_already_uploaded()
    pending = [f for f in media if os.path.basename(f) not in already]
    print(f'Ja pujats: {len(media) - len(pending)}')
    print(f'Pendents:  {len(pending)}')
    print()

    if not pending:
        print('Tot ja pujat!')
        return

    errors = []
    for i, filepath in enumerate(pending, 1):
        filename = os.path.basename(filepath)
        print(f'[{i}/{len(pending)}] Pujant: {filename}')
        result = subprocess.run(
            [IA_EXE, 'upload', ITEM_ID, filepath,
             '--metadata', 'mediatype:image',
             '--metadata', 'subject:Validated ID',
             '--metadata', 'subject:Instagram',
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

if __name__ == '__main__':
    main()
