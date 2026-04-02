"""
wait_and_run.py
Executa els passos 1-4 de la integracio de Twitter amb notificacions Telegram.

El pas 1 original (archive_twitter_youtube.py) ja ha acabat (exit 0).
Aquest script:
  1. Re-executa archive_twitter_youtube.py (reintenta els 3 fallits)
  2. upload_twitter_media.py
  3. parse_twitter.py
  4. generate.py
"""

import subprocess
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

from tg_notify import notify

PYTHON = sys.executable
HERE   = os.path.dirname(os.path.abspath(__file__))


def run_step(label, script, step_num):
    notify(f'[{step_num}/4] Iniciant: {label}...')
    print(f'\n{"="*60}\nPAS {step_num}: {label}\n{"="*60}')
    result = subprocess.run(
        [PYTHON, os.path.join(HERE, script)],
        cwd=HERE,
        encoding='utf-8',
        errors='replace',
    )
    if result.returncode != 0:
        notify(f'ERROR al pas {step_num}: {label} (codi {result.returncode})')
        return False
    return True


notify('Supervisor iniciat. Llancant passos 1-4...')

# Pas 1: reintenta els videos fallits (salta els ja arxivats)
if not run_step('Arxivar videos YouTube (reintent fallits)', 'archive_twitter_youtube.py', 1):
    sys.exit(1)

# Pas 2
if not run_step('Pujar media Twitter a Archive.org', 'upload_twitter_media.py', 2):
    sys.exit(1)

# Pas 3
if not run_step('Generar data/twitter.json', 'parse_twitter.py', 3):
    sys.exit(1)

# Pas 4
if not run_step('Generar HTML (twitter + imatges + videos)', 'generate.py', 4):
    sys.exit(1)

notify('Tot completat! twitter.html, imatges.html i videos.html actualitzats.')
print('\nFet!')
