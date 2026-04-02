# Validated ID — Arxiu Històric

Projecte de preservació i publicació de l'historial de xarxes socials de Validated ID (empresa de firma digital i identitat electrònica, fundada 2012, adquirida per Signaturit Group 2025).

## Estructura del projecte

```
validated-id-history/
├── data/
│   ├── linkedin.json          # 1.784 posts LinkedIn
│   ├── instagram.json         # 105 posts Instagram
│   ├── facebook.json          # 845 posts Facebook
│   ├── twitter.json           # 2.015 posts Twitter (generat per parse_twitter.py)
│   ├── videos_youtube.json    # Vídeos YouTube arxivats a Archive.org
│   ├── videos_facebook.json   # Vídeos Facebook a Archive.org
│   ├── twitter_media_index.json  # 1.613 fitxers media Twitter → Archive.org URLs
│   └── twitter_yt_classify.json  # Classificació vídeos YT de Twitter (propi/extern)
├── assets/                    # Logos, imatges estàtiques
├── generate.py                # Generador principal de tot l'HTML
├── lang_detect.py             # Detecció d'idioma (lingua library)
├── parse_linkedin.py          # Parseja backup LinkedIn → data/linkedin.json
├── parse_facebook.py          # Parseja backup Facebook → data/facebook.json
├── parse_instagram.py         # Parseja backup Instagram → data/instagram.json
├── parse_twitter.py           # Parseja backup Twitter → data/twitter.json
├── archive_twitter_youtube.py # Arxiva vídeos YouTube de Twitter a Archive.org
├── upload_twitter_media.py    # Puja fotos/vídeos Twitter a Archive.org
├── tg_notify.py               # Notificacions Telegram (bot SantiAssistantBot)
├── wait_and_run.py            # Supervisor seqüencial amb notificacions
├── index.html                 # Pàgina principal (editada manualment)
├── linkedin.html              # Generat per generate.py
├── instagram.html             # Generat per generate.py (grid de targetes)
├── facebook.html              # Generat per generate.py
├── twitter.html               # Generat per generate.py (grid de targetes)
├── imatges.html               # Galeria unificada (generat per generate.py)
└── videos.html                # Vídeos unificats (generat per generate.py)
```

## Xarxes socials incloses

| Xarxa | Posts | Notes |
|-------|-------|-------|
| LinkedIn | 1.784 | Compte empresa |
| Facebook | 845 | Compte empresa |
| Instagram | 105 | Compte empresa |
| Twitter/X | 2.015 | 3 comptes: @ValidatedID, @VIDsigner, @VIDidentity |

## Twitter — detalls tècnics

**Backup local:** `C:\Users\santi\Dropbox\Social VID\Twitter\`
- 3 carpetes: `ValidatedID/`, `VIDsigner/`, `VIDidentity/`
- Format: `tweets.js`, `account.js`, media a `tweets_media/`
- Noms media: `{tweet_id}-{hash}.ext`
- Dates: `"Mon Jan 01 12:00:00 +0000 2020"`

**Filtratge:** sense RTs (comencen per `RT @`), sense respostes (comencen per `@`)

**Comptes i colors:**
```python
TWITTER_ACCOUNT_COLORS = {
    'ValidatedID': '#1d9bf0',
    'VIDsigner':   '#7c3aed',
    'VIDidentity': '#059669'
}
```

**filterKey** per imatges/vídeos: `x:ValidatedID`, `x:VIDsigner`, `x:VIDidentity`
**Etiquetes UI:** `x:@ValidatedID`, `x:@VIDsigner`, `x:@VIDidentity`

## LinkedIn — detalls tècnics

**Backup local:** `C:\Users\santi\Dropbox\Social VID\Linkedin\backup\`
- Fitxers: `02_posts_YYYY.json` (un per any), `media/` amb imatges i vídeos
- Vídeos natius: fitxers `urn_li_ugcPost_XXXX_video.mp4` a `media/`
- `parse_linkedin.py` detecta automàticament els vídeos natius i els separa de les imatges

## Archive.org

**Items creats:**
- `validatedid-twitter-media` — 1.613 fitxers (fotos + vídeos MP4 Twitter)
- `validatedid-linkedin-media` — imatges + 26 vídeos natius MP4 LinkedIn
- `validatedid-youtube-channel` — vídeos propis de YouTube
- `externs-youtube-channel` — vídeos externs de YouTube
- `validatedid-facebook-media` — imatges + vídeos MP4 Facebook
- `validatedid-instagram-media` — imatges Instagram

**Format de thumbnails per vídeos:**
- Twitter/Facebook: `{ARCHIVE_BASE}/{filename}.mp4.jpg` (pujat manualment)
- LinkedIn: `{ARCHIVE_BASE}/validatedid-linkedin-media.thumbs/{filename_sense_ext}_000001.jpg` (generat automàticament per Archive.org)

**Eina d'upload:** `ia.exe` (path complet necessari):
```
C:\Users\santi\AppData\Local\Python\pythoncore-3.14-64\Scripts\ia.exe
```
Flags correctes: `-m KEY:VALUE`, `-R 5`, `-s 10`
**IMPORTANT:** No fer uploads concurrents — causa que l'ítem quedi buit.

## Generació HTML

```bash
python generate.py
```

Genera tots els fitxers HTML. Llegeix els JSONs de `data/` i produeix:
- `linkedin.html`, `facebook.html` — format llista (text + media lateral)
- `instagram.html`, `twitter.html` — format grid de targetes
- `imatges.html` — galeria unificada de totes les xarxes
- `videos.html` — vídeos de YouTube + Facebook + Twitter + LinkedIn natius

**`index.html` s'edita manualment** — no es regenera amb `generate.py`.

## Format de dades

Les imatges als JSONs tenen formats diferents segons la xarxa:
- LinkedIn, Instagram, Facebook: llista de strings (URLs)
- Twitter: llista d'objectes `{url: '...', alt: '...'}` → `generate.py` normalitza a strings

## Detecció d'idioma

`lang_detect.py` usa la llibreria `lingua` amb:
- Idiomes: ES, EN, DE, FR, CA, PT
- Threshold: `with_minimum_relative_distance(0.35)`
- Pre-processa: elimina URLs, hashtags, mencions, chars Unicode de control, cadenes de noms propis

## Estat actual (abril 2026)

- Totes les pàgines generades i funcionals
- 2.015 tweets parsejats, 1.613 fitxers media a Archive.org
- 26 vídeos natius LinkedIn pujats a Archive.org i integrats a `videos.html`
- 30 vídeos YouTube arxivats (1 falla: `#DayoneWebinar zbD3e6nxw-s` — eliminat de YT)
- Disseny responsive per a mòbils a totes les pàgines

## Pendent

- **`historia.html`** — revisió i actualització del contingut
