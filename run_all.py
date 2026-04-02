"""
run_all.py
Supervisor que executa els passos 1-5 de la integracio de Twitter
i envia notificacions a Telegram.

Pas 1: archive_twitter_youtube.py  (ja esta corrent, esperem que acabi)
Pas 2: upload_twitter_media.py
Pas 3: parse_twitter.py
Pas 4+5: generate.py (genera twitter.html i actualitza imatges/videos)
"""

import subprocess
import sys
import os
import time
from tg_notify import notify

sys.stdout.reconfigure(encoding='utf-8')

PYTHON = sys.executable
HERE   = os.path.dirname(os.path.abspath(__file__))

def run_step(name, script, step_num, total=4):
    notify(f"[{step_num}/{total}] Iniciant: {name}...")
    print(f"\n{'='*60}")
    print(f"PAS {step_num}: {name}")
    print(f"{'='*60}")
    result = subprocess.run(
        [PYTHON, os.path.join(HERE, script)],
        cwd=HERE,
        encoding='utf-8',
        errors='replace',
    )
    if result.returncode == 0:
        notify(f"[{step_num}/{total}] OK: {name}")
        return True
    else:
        notify(f"[{step_num}/{total}] ERROR en: {name} (codi {result.returncode})")
        return False


# ── Pas 1: archive_twitter_youtube.py ────────────────────────────────────────
# Ja esta corrent en background (task b8qx25317).
# Esperem que acabi comprovant si videos_youtube.json canvia
# o simplement el tornem a llançar (salta els ja arxivats).

notify("Supervisor iniciat. Llancant pas 1 (arxivar YouTube)...")

if not run_step("Arxivar videos YouTube de Twitter", "archive_twitter_youtube.py", 1):
    notify("Aturant per error al pas 1.")
    sys.exit(1)

# ── Pas 2: upload_twitter_media.py ───────────────────────────────────────────
if not run_step("Pujar media de Twitter a Archive.org", "upload_twitter_media.py", 2):
    notify("Aturant per error al pas 2.")
    sys.exit(1)

# ── Pas 3: parse_twitter.py ──────────────────────────────────────────────────
if not run_step("Generar data/twitter.json", "parse_twitter.py", 3):
    notify("Aturant per error al pas 3.")
    sys.exit(1)

# ── Pas 4+5: generate.py ─────────────────────────────────────────────────────
if not run_step("Generar HTML (twitter.html + imatges + videos)", "generate.py", 4):
    notify("Aturant per error al pas 4.")
    sys.exit(1)

notify("Tot completat! twitter.html, imatges.html i videos.html actualitzats.")
print("\nFet!")
