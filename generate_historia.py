"""
generate_historia.py
Genera historia.html — cronologia de Validated ID 2012–2025.
Us: python generate_historia.py
"""

import json
import os
import sys
from html import escape

# Importem els components comuns de generate.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate import html_header, html_footer, COMMON_CSS


def esc(t):
    return escape(str(t), quote=True)


def eschtml(t):
    return escape(str(t))


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def truncate(text, n=140):
    if not text:
        return ''
    s = str(text)
    return s[:n].rstrip() + ('…' if len(s) > n else '')


def fmt_date(d):
    """YYYY-MM-DD → DD/MM/YYYY"""
    try:
        return f'{d[8:10]}/{d[5:7]}/{d[:4]}'
    except Exception:
        return d


# ── NARRATIVES PER ANY ────────────────────────────────────────────────────────

YEARS = [str(y) for y in range(2012, 2026)]

YEAR_NARRATIVES = {
    '2012': (
        'En febrero, Santi Casas, Iván Basart y Fernando Pino fundan Validated ID, '
        'con experiencia previa en certificación digital y firma electrónica. A finales de '
        'año se incorpora Jaume Fuentes, con amplio historial en ventas en el sector TIC. '
        'Modelo bootstrap: los primeros ingresos vienen de proyectos como expertos. Se hereda '
        '<strong>pimefactura</strong>, operada conjuntamente con PIMEC. Primeros despliegues de '
        '<strong>VIDsigner</strong> en el sector salud — el Institut Lleida d\'Oftalmologia es '
        'el primer cliente, con cobertura en TV3.'
    ),
    '2013': (
        'VIDsigner gana tracción real: integración con SAP via NewLog/Seidor, firma digital en '
        'el Ajuntament de Barcelona y Terrassa. El <strong>consentimiento informado digital</strong> '
        'emerge como caso de uso principal en sanidad. Presencia en TicSalut, ACES y el ecosistema '
        'de salud catalán.'
    ),
    '2014': (
        'Primera aparición en el <strong>Mobile World Congress</strong>. La compañía '
        '<strong>triplica su volumen de negocio</strong>. Nuevos clientes en sanidad pública y '
        'privada, y primeras implantaciones en administración local. El Consell de la UE aprueba '
        'el reglamento eIDAS — Validated ID lo sigue de cerca desde el principio.'
    ),
    '2015': (
        'Foco en salud: hospitales, clínicas, campañas "clínica sin papeles". Santi Casas '
        'entrevistado en Expansión sobre biometría y firma electrónica. Seleccionados en la '
        '<strong>Fase 1 de Horizon 2020</strong> (Sello de Excelencia). Misión comercial a '
        'Países Bajos con ACCIÓ. Acuerdo de colaboración con ACES.'
    ),
    '2016': (
        'Ronda <strong>FFF</strong>. En el MWC se presenta la app para firmar con el DNIe 3.0 '
        'via NFC desde el móvil, lanzada como servicio gratuito en '
        '<strong>firmacontuDNIe.es</strong> — cubierto por RTVE / Marca España. '
        'Segundo Sello de Excelencia H2020. Crecimiento del canal de partners en '
        'administración pública.'
    ),
    '2017': (
        'Nace <strong>VIDchain</strong>, la apuesta por la identidad digital soberana basada '
        'en blockchain — el modelo que años después se convertiría en el estándar EUDIW. '
        'La compañía supera los <strong>300 clientes</strong> y los '
        '<strong>500.000 documentos firmados al año</strong>. '
        'Seleccionados para el acelerador <strong>Cuatrecasas Acelera</strong>.'
    ),
    '2018': (
        '<strong>Ganadores de la II edición de Cuatrecasas Acelera</strong>. VIDchain se '
        'presenta a inversores en el 4YFN del MWC. Se unen a <strong>Alastria</strong> y ganan '
        'el DemoDay de Alastria en Cataluña. Seleccionados entre los 5 mejores startups '
        'catalanas para el <strong>Slush</strong> de Helsinki. Expansión internacional: '
        'Crèdit Andorrà y DocuWare Alemania. Clientes de referencia como el '
        'Hospital Sant Joan de Déu.'
    ),
    '2019': (
        'Ronda de inversión con <strong>Randstad Innovation Fund, Caixa Capital Risc y '
        'Cuatrecasas Ventures</strong> para consolidar el canal indirecto y acelerar VIDchain. '
        'Organizan el <strong>Rebooting Web of Trust 8</strong> en Barcelona. VIDchain, entre '
        'los 24 finalistas del premio <strong>EIC "Blockchain for Social Good"</strong> '
        '(178 candidatos, 43 países). Inicio de la colaboración con la Comisión Europea en '
        'el proyecto <strong>EBSI</strong>.'
    ),
    '2020': (
        'Respuesta al COVID-19: <strong>firmas ilimitadas gratuitas</strong> para cualquier '
        'organización. Trabajo activo en el <strong>ESSIF</strong> (European Self-Sovereign '
        'Identity Framework) dentro de EBSI. Ivan Basart en el jurado de la European Blockchain '
        'Convention junto a representantes de Banco Santander y Mastercard.'
    ),
    '2021': (
        'El <strong>4 de junio</strong>, la UE anuncia el marco de la European Digital Identity '
        'Wallet: exactamente el modelo que Validated ID llevaba cuatro años construyendo. '
        '<strong>Ganadores de Start4Big</strong> (192 proyectos compitiendo, con CaixaBank, '
        'SEAT y Telefónica entre los socios). Financiación <strong>CDTI</strong> para VIDchain.'
    ),
    '2022': (
        '<strong>VIDchain es la primera solución del mundo en ser conforme con EBSI</strong>, '
        'cubriendo los cuatro casos de uso (diploma, carné estudiantil, identidad, PDA1). '
        'Primera certificación <strong>HDS en Francia</strong> para un proveedor de firma '
        'electrónica. <strong>600 municipios</strong> en España usan VIDsigner.'
    ),
    '2023': (
        'VIDwallet repite conformidad EBSI: <strong>el único wallet con los cuatro casos de '
        'uso superados</strong>. Seleccionados para el <strong>EWC Large Scale Pilot</strong> '
        '(60+ socios europeos liderado por Suecia y Finlandia). Más de '
        '<strong>23.000 empresas y autónomos</strong> usan pimefactura.'
    ),
    '2024': (
        'Transferencia de pimefactura a <strong>B2Brouter</strong>, en acuerdo con PIMEC. '
        'La compañía se focaliza en eIDAS2 como <strong>qTSP</strong> (Qualified Trust Service '
        'Provider). El producto VIDchain/VIDwallet pasa a llamarse <strong>VIDidentity</strong>. '
        'Más de <strong>3.000 clientes</strong> VIDsigner y <strong>150+ integraciones</strong> '
        'con Sage, DocuWare, SAP, Salesforce y Microsoft.'
    ),
    '2025': (
        'En febrero se anuncia la incorporación a <strong>Signaturit Group</strong>; en mayo '
        'se cierra oficialmente. Signaturit se integra a su vez en <strong>Namirial</strong>, '
        'configurando así el <strong>principal prestador de servicios de confianza de Europa</strong>. '
        'El último hito como Validated ID independiente: la firma del acuerdo institucional '
        'para promover Gobiernos Locales Inteligentes en el Congrés de Govern Digital de '
        'Barcelona, con la Generalitat, el Ajuntament de Barcelona, las cuatro Diputaciones, '
        'AOC y Localret — firmado con VIDsignerBIO.'
    ),
}

MILESTONES = {
    '2012': 'Fundación',
    '2016': 'Ronda FFF',
    '2018': 'Premio Cuatrecasas',
    '2019': 'Ronda inversores',
    '2021': 'EUDIW anunciado',
    '2022': 'Primeros EBSI conformant',
    '2025': 'Adquisición Signaturit',
}

# ── SELECCIÓ DE POSTS PER ANY ─────────────────────────────────────────────────
# Format: [(network, [keywords]), ...]  — s'agafa el primer post que coincideixi,
# preferint els que tinguin imatge.

YEAR_POST_SEARCHES = {
    '2012': [
        ('linkedin', ['Institut Lleida', 'ILO', 'TV3']),
        ('linkedin', ['BDigital', 'ViDSigner']),
        ('twitter',  ['ILO', 'Institut Lleida', 'ViDSigner', 'primer']),
    ],
    '2013': [
        ('linkedin', ['NewLog', 'SAP', 'firma biométrica']),
        ('linkedin', ['Ajuntament de Barcelona', 'ViDSigner']),
        ('linkedin', ['TicSalut', 'consentimiento']),
    ],
    '2014': [
        ('linkedin', ['MWC', 'Mobile World']),
        ('linkedin', ['triplicando', 'volumen de negocio', 'triplica']),
        ('twitter',  ['MWC14', 'ViDSigner', 'Surface']),
    ],
    '2015': [
        ('linkedin', ['Horizon', 'H2020', 'Sello de Excelencia', 'SME Instrument']),
        ('linkedin', ['ACES', 'acuerdo', 'Monset']),
        ('linkedin', ['Expansión', 'entrevista', 'biometría']),
    ],
    '2016': [
        ('linkedin', ['DNIe', 'NFC', 'DNI 3.0', 'firmacontudnie']),
        ('twitter',  ['DNIe', 'NFC', 'DNI 3.0']),
        ('linkedin', ['MWC', 'firmar', 'móvil']),
    ],
    '2017': [
        ('linkedin', ['VIDchain', 'self-sovereign', 'identidad digital soberana', 'blockchain']),
        ('linkedin', ['300 clientes', '500.000', 'EFE']),
        ('linkedin', ['Cuatrecasas', 'Acelera', 'seleccionados']),
    ],
    '2018': [
        ('linkedin', ['Cuatrecasas Acelera', 'ganadores', 'ganador', 'II edición']),
        ('linkedin', ['Alastria', 'DemoDay', 'ganado', 'won']),
        ('linkedin', ['Slush', 'Helsinki', 'Top 5']),
    ],
    '2019': [
        ('linkedin', ['Caixa Capital', 'Randstad', 'inversión', 'ronda']),
        ('linkedin', ['Blockchain for Social Good', 'EIC', 'finalistas', 'finalist']),
        ('linkedin', ['Rebooting', 'Web of Trust', 'RWoT']),
    ],
    '2020': [
        ('linkedin', ['COVID', 'gratuito', 'ilimitad', 'coronavirus']),
        ('linkedin', ['EBSI', 'ESSIF', 'European Self-Sovereign']),
        ('linkedin', ['European Blockchain Convention', 'jury', 'jurado']),
    ],
    '2021': [
        ('linkedin', ['European Digital Identity Wallet', 'four years', 'cuatro años']),
        ('linkedin', ['Start4Big', 'ganadores', 'winner', 'winners']),
        ('linkedin', ['CDTI', 'financiación', 'VIDchain']),
    ],
    '2022': [
        ('linkedin', ['EBSI', 'compliant', 'first solution', 'primera solución']),
        ('linkedin', ['HDS', 'France', 'Francia']),
        ('linkedin', ['600', 'municipios', 'ayuntamientos']),
    ],
    '2023': [
        ('linkedin', ['EBSI', 'compliant', 'four use cases', 'ONLY']),
        ('linkedin', ['EWC', 'large scale', 'Large Scale', 'pilot']),
        ('linkedin', ['pimefactura', '23.000', 'factura']),
    ],
    '2024': [
        ('linkedin', ['B2Brouter', 'pimefactura', 'PIMEC']),
        ('linkedin', ['qTSP', 'QTSP', 'Qualified Trust']),
        ('linkedin', ['3.000', '3000', 'integraciones', 'clientes']),
    ],
    '2025': [
        ('linkedin', ['Signaturit', 'joins', 'une fuerzas', 'familia']),
        ('linkedin', ['oficial', 'adquisición', 'aprobada', 'firmó']),
        ('linkedin', ['Acord Institucional', 'acte de signatura', 'CGD2025']),
    ],
}

NETWORK_COLORS = {
    'linkedin':  '#0077b5',
    'twitter':   '#1da1f2',
    'facebook':  '#1877f2',
    'instagram': '#c13584',
}
NETWORK_LABELS = {
    'linkedin':  'LinkedIn',
    'twitter':   'Twitter/X',
    'facebook':  'Facebook',
    'instagram': 'Instagram',
}


# ── HELPERS ───────────────────────────────────────────────────────────────────

def get_img(p):
    imgs = p.get('images', [])
    if not imgs:
        return None
    img = imgs[0]
    return img['url'] if isinstance(img, dict) else img


def find_post(idx, network, year, keywords):
    """Cerca el millor post (preferint els que tenen imatge)."""
    candidates = idx.get((network, year), [])
    with_img, without_img = [], []
    for p in candidates:
        text = (p.get('text') or '').lower()
        if any(kw.lower() in text for kw in keywords):
            if get_img(p):
                with_img.append(p)
            else:
                without_img.append(p)
    return (with_img or without_img or [None])[0]


def post_card_html(p):
    net    = p['network']
    color  = NETWORK_COLORS.get(net, '#2a3a5a')
    label  = NETWORK_LABELS.get(net, net)
    anchor = p['anchor']
    href   = f'{net}.html#{anchor}'
    img    = get_img(p)
    text   = truncate(p.get('text') or '')
    date   = fmt_date(p.get('date', '')[:10])

    img_html = (f'<img class="pc-img" src="{esc(img)}" loading="lazy" alt="">'
                if img else '<div class="pc-no-img"></div>')

    return (
        f'<a class="pc" href="{esc(href)}">'
        f'{img_html}'
        f'<div class="pc-body">'
        f'<div class="pc-badges">'
        f'<span class="pc-net" style="background:{color}">{eschtml(label)}</span>'
        f'</div>'
        f'<div class="pc-text">{eschtml(text)}</div>'
        f'<div class="pc-date">{esc(date)}</div>'
        f'</div>'
        f'</a>'
    )


# ── GENERADOR PRINCIPAL ───────────────────────────────────────────────────────

def generate_historia():
    # Carreguem tots els posts
    all_posts = []
    for net in ['linkedin', 'instagram', 'facebook', 'twitter']:
        path = f'data/{net}.json'
        if os.path.exists(path):
            posts = load_json(path)
            for p in posts:
                p['network'] = net
            all_posts.extend(posts)

    # Índex per (network, year)
    idx = {}
    for p in all_posts:
        key = (p['network'], p['year'])
        idx.setdefault(key, []).append(p)

    # Seccions del timeline
    timeline_html = ''
    for year in YEARS:
        narrative = YEAR_NARRATIVES.get(year, '')
        milestone = MILESTONES.get(year)
        searches  = YEAR_POST_SEARCHES.get(year, [])

        # Fins a 3 posts representatius (sense duplicats)
        found, seen = [], set()
        for net, keywords in searches:
            if len(found) >= 3:
                break
            p = find_post(idx, net, year, keywords)
            if p and p['anchor'] not in seen:
                found.append(p)
                seen.add(p['anchor'])

        # Només mostrem targetes amb imatge
        found = [p for p in found if get_img(p)]
        cards_html = ''
        if found:
            cards_html = (
                '<div class="pc-grid">'
                + ''.join(post_card_html(p) for p in found)
                + '</div>'
            )

        milestone_html = (
            f'<div class="milestone-tag">{eschtml(milestone)}</div>'
            if milestone else ''
        )

        timeline_html += f"""
<div class="year-section" id="y{year}">
  <div class="year-marker">
    <div class="year-dot"></div>
    <span class="year-num">{year}</span>
  </div>
  <div class="year-content">
    {milestone_html}
    <p class="year-narrative">{narrative}</p>
    {cards_html}
  </div>
</div>"""

    HISTORIA_CSS = """
  /* ── Historia layout ── */
  .historia-wrap {
    max-width: 940px;
    margin: 0 auto;
    padding: 2rem 1.5rem 3rem;
  }
  .historia-title {
    font-size: 2rem; font-weight: 700; color: #e6f0ff;
    margin-bottom: 0.4rem;
  }
  .historia-subtitle {
    font-size: 1rem; font-weight: 600; color: #00BF71;
    margin-bottom: 0.8rem; letter-spacing: 0.3px;
  }
  .historia-intro {
    font-size: 0.95rem; color: #8892b0; line-height: 1.65;
    max-width: 680px; margin-bottom: 2.5rem;
  }

  /* ── Timeline ── */
  .timeline { position: relative; padding-left: 2.5rem; }
  .timeline::before {
    content: '';
    position: absolute; left: 5px; top: 6px; bottom: 0;
    width: 2px;
    background: linear-gradient(to bottom, #00BF71 0%, #1e2a4a 100%);
  }

  .year-section { position: relative; padding: 0 0 2.5rem 1.5rem; }
  .year-section::before {
    content: '';
    position: absolute; left: -10px; top: 6px;
    width: 14px; height: 14px; border-radius: 50%;
    background: #00BF71; border: 3px solid #151A35;
    box-shadow: 0 0 0 2px #00BF71;
    z-index: 1;
  }

  .year-marker {
    display: flex; align-items: center; gap: 0.6rem;
    margin-bottom: 0.6rem;
  }
  .year-dot { display: none; }
  .year-num {
    font-size: 1.4rem; font-weight: 700; color: #00BF71; line-height: 1;
  }
  .milestone-tag {
    display: inline-block;
    background: #00BF71; color: #0d1229;
    font-size: 0.6rem; font-weight: 700;
    padding: 0.15rem 0.6rem; border-radius: 10px;
    text-transform: uppercase; letter-spacing: 0.6px;
    margin-bottom: 0.5rem;
  }
  .year-narrative {
    font-size: 0.9rem; color: #ccd6f6; line-height: 1.7;
    margin-bottom: 0.9rem; max-width: 700px;
  }
  .year-narrative strong { color: #e6f0ff; }

  /* ── Post cards ── */
  .pc-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 0.75rem;
  }
  .pc {
    background: #1e2a4a; border: 1px solid #2a3a5a;
    border-radius: 8px; overflow: hidden;
    text-decoration: none; display: flex; flex-direction: column;
    transition: border-color 0.15s, transform 0.15s;
  }
  .pc:hover { border-color: #00BF71; transform: translateY(-2px); }
  .pc-img {
    width: 100%; aspect-ratio: 16/9;
    object-fit: cover; display: block;
  }
  .pc-no-img {
    width: 100%; aspect-ratio: 16/9;
    background: #0d1229;
  }
  .pc-body {
    padding: 0.55rem 0.7rem;
    display: flex; flex-direction: column; gap: 0.3rem; flex: 1;
  }
  .pc-net {
    font-size: 0.6rem; font-weight: 700;
    padding: 0.1rem 0.4rem; border-radius: 3px; color: #fff;
    display: inline-block;
  }
  .pc-text {
    font-size: 0.75rem; color: #8892b0; line-height: 1.45; flex: 1;
  }
  .pc-date { font-size: 0.63rem; color: #4a5a7a; }

  /* ── Year nav ── */
  .year-nav {
    display: flex; flex-wrap: wrap; gap: 0.4rem;
    margin-bottom: 2.2rem; list-style: none; padding: 0;
  }
  .year-nav a {
    background: #1a2a4a; color: #8892b0;
    border: 1px solid #2a3a5a; border-radius: 4px;
    font-size: 0.75rem; font-weight: 600; padding: 0.2rem 0.55rem;
    text-decoration: none; transition: all 0.15s;
  }
  .year-nav a:hover { background: #00BF71; color: #0d1229; border-color: #00BF71; }

  /* ── Epilogue ── */
  .epilogue {
    margin-top: 3rem; padding: 1.5rem 1.75rem;
    background: #1a2a4a; border: 1px solid #2a3a5a; border-radius: 10px;
    max-width: 700px;
  }
  .epilogue-title {
    font-size: 0.8rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.8px; color: #00BF71; margin-bottom: 1.1rem;
  }
  .epilogue-stats {
    display: flex; flex-wrap: wrap; gap: 1.5rem;
  }
  .stat { display: flex; flex-direction: column; align-items: center; min-width: 80px; }
  .stat-num {
    font-size: 2rem; font-weight: 700; color: #e6f0ff; line-height: 1;
  }
  .stat-label { font-size: 0.75rem; color: #8892b0; margin-top: 0.2rem; }

  /* ── Responsive ── */
  @media (max-width: 600px) {
    .timeline { padding-left: 1.5rem; }
    .year-section { padding-left: 1rem; }
    .historia-title { font-size: 1.5rem; }
    .pc-grid { grid-template-columns: repeat(2, 1fr); }
  }
  @media (max-width: 360px) {
    .pc-grid { grid-template-columns: 1fr; }
  }
"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Validated ID — Historia</title>
<style>
{COMMON_CSS}
{HISTORIA_CSS}
</style>
</head>
<body>

{html_header('Historia de Validated ID', 'Historia')}

<div class="historia-wrap">
  <h1 class="historia-title">Historia de Validated ID</h1>
  <p class="historia-subtitle">Un caso de éxito</p>
  <p class="historia-intro">
    Una startup de firma electrónica nacida en Barcelona en 2012 que, en poco más de una década,
    pasó de sus primeros clientes en el sector salud a convertirse en referente europeo en
    identidad digital, participar en los proyectos de la Comisión Europea que definieron el
    estándar EUDIW, y sumar más de 5.000 clientes en más de 40 países. Una historia de tecnología,
    convicción y un equipazo que solo podía terminar integrándose en el líder de los servicios
    de confianza europeo.
  </p>

  <nav class="year-nav" aria-label="Saltar a año">
    {''.join(f'<a href="#y{y}">{y}</a>' for y in YEARS)}
  </nav>

  <div class="timeline">
    {timeline_html}
  </div>

  <div class="epilogue">
    <div class="epilogue-title">En el momento de la integración en Signaturit (2025)</div>
    <div class="epilogue-stats">
      <div class="stat"><span class="stat-num">5.000</span><span class="stat-label">clientes</span></div>
      <div class="stat"><span class="stat-num">350</span><span class="stat-label">partners</span></div>
      <div class="stat"><span class="stat-num">20M</span><span class="stat-label">firmas / año</span></div>
    </div>
  </div>
</div>

{html_footer()}

</body>
</html>"""

    return html


# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    html = generate_historia()
    with open('historia.html', 'w', encoding='utf-8') as f:
        f.write(html)
    size = os.path.getsize('historia.html') / 1024
    print(f'✓ historia.html ({size:.0f} KB)')
