"""
tag_fb_langs.py
Detecta l'idioma dels vídeos de Facebook i actualitza data/videos_facebook.json.
"""
import sys, json, re
sys.stdout.reconfigure(encoding='utf-8')


def detect_lang(title):
    if not title or not title.strip():
        return 'ES'  # majoria son castellà

    t = title.strip()

    # Castellà: caràcters inconfusibles
    if re.search(r'[¿¡ñÑ]', t):
        return 'ES'
    if re.search(r'\b(también|más|está|están|nuestro|nuestra|gracias|para|que|los|las|del|por|hoy|vuelve|siempre|ahora|todo|todos|cómo|qué|puede|permite|permiten|sigue|igual|nuevo|nueva|desde|datos|firma|firmar|inscríbete|descubre|comunícate)\b', t, re.I):
        return 'ES'

    # Alemany: Umlauts o paraules úniques
    if re.search(r'[üÜöÖäÄß]', t):
        return 'DE'
    if re.search(r'\b(Die|Der|Das|Ein|Eine|Alle|Als|Um|Wir|und|mit|für|von|im|zur|ist|sind|Daten|Rahmen|Zusammen|Partnerschaft|internationaler|Partner)\b', t):
        return 'DE'

    # Francès: contraccions i paraules úniques
    if re.search(r"\bd'[aeiouàâèéêëîïôùûü]|l'[aeiouàâèéêëîïôùûü]|qu'[aeiou]", t, re.I):
        return 'FR'
    if re.search(r'\b(Nous|nous|ravis|Vendredi|permettent|différents|réduire|types)\b', t, re.I):
        return 'FR'

    # Per defecte: anglès
    return 'EN'


data = json.load(open('data/videos_facebook.json', encoding='utf-8'))

counts = {}
for fn, d in data.items():
    lang = detect_lang(d['title'])
    d['lang'] = lang
    counts[lang] = counts.get(lang, 0) + 1
    print(f'{lang}  {d["title"][:70]}')

print()
print('Resum:', counts)

with open('data/videos_facebook.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print('Actualitzat data/videos_facebook.json')
