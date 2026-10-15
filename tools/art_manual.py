"""Art Bible section extensions for the existing source-driven manual renderer."""
from __future__ import annotations
import html
import json
import os
from pathlib import Path


def read(root, name):
    return json.loads((root / ('sources/art-bible/' + name + '.json')).read_text(encoding='utf-8'))


def art_pages(root):
    return read(root, 'chapters')['pages']


def integrate_art_links(pages, root):
    additions = read(root, 'chapters')['integrations']
    for page in pages:
        if page['path'] in additions:
            page['sections'].insert(0, {'title': 'Current art-production authority', 'paragraphs': [additions[page['path']]], 'links': ['[[art-style/index.html|Briarwake — Official Pixel Art Bible]]', '[[art-style/godot.html|Godot 2D Art Integration Standards]]']})
    return pages


def relative(current, target):
    return os.path.relpath(target, os.path.dirname(current)).replace(os.sep, '/')


def attr(value):
    return html.escape(str(value), quote=True)


def figure(record, path, caption=None):
    src = relative(path, record['path'])
    identifier = record['id']
    return f'''<figure class="art-figure"><a href="gallery.html#ref-{attr(identifier)}"><img src="{attr(src)}" width="{record['dimensions'][0]}" height="{record['dimensions'][1]}" style="width:{record['dimensions'][0] * 2}px" loading="lazy" alt="{attr(record['category'] + ': ' + identifier + '. ' + record['rules'])}"></a><figcaption><span class="art-label">{attr(record['status'])}</span> {html.escape(caption or record['rules'])} <small>{record['dimensions'][0]}×{record['dimensions'][1]} native pixels · <a href="gallery.html#ref-{attr(identifier)}">Inspect reference</a></small></figcaption></figure>'''


def viewer(record, path):
    width, height = record['dimensions']
    return f'''<div class="pixel-viewer" data-width="{width}" data-height="{height}"><div class="art-controls"><label>Zoom <select data-zoom aria-label="Zoom {attr(record['id'])}"><option value="1">1×</option><option value="2" selected>2×</option><option value="4">4×</option><option value="8">8×</option></select></label><label><input type="checkbox" data-pixel-grid> Pixel grid</label><label><input type="checkbox" data-tile-grid> 16-pixel grid</label><label><input type="checkbox" data-checker checked> Checkerboard</label></div><div class="pixel-scroll"><div class="pixel-stage" style="width:{width * 2}px;height:{height * 2}px;--zoom:2"><img src="{attr(relative(path, record['path']))}" width="{width}" height="{height}" alt="{attr(record['rules'])}" loading="lazy"><div class="pixel-grid" aria-hidden="true"></div><div class="tile-grid" aria-hidden="true"></div></div></div></div>'''


def render_art_section(section, path, root):
    records = read(root, 'references')['assets']
    by_id = {r['id']: r for r in records}
    parts = []
    if section.get('figures'):
        parts.append('<div class="art-figures">' + ''.join(figure(by_id[f['asset']], path, f.get('caption')) for f in section['figures']) + '</div>')
    widget = section.get('widget')
    palette = read(root, 'palette')
    if widget in {'palette', 'palette-preview'}:
        selected = palette['colors'] if widget == 'palette' else palette['colors'][:16]
        parts.append('<p class="art-note">Study 01 · Proposed reference · Select a swatch to copy its hex value. RGB and material uses remain available as text.</p><p class="copy-status" role="status"></p><div class="palette-grid">')
        for c in selected:
            parts.append(f'''<button type="button" class="swatch" data-copy="{c['hex']}" aria-label="Copy {c['name']} {c['hex']}"><span style="background:{c['hex']}" aria-hidden="true"></span><strong>{c['name']}</strong><code>{c['hex']}</code><small>RGB {', '.join(str(x) for x in c['rgb'])}</small></button>''')
        parts.append('</div>')
        if widget == 'palette':
            parts.append('<details><summary>Complete color usage specification</summary><div class="table-scroll" tabindex="0" role="region" aria-label="Color specification"><table><thead><tr><th scope="col">Color</th><th scope="col">Hex / RGB</th><th scope="col">Material / use</th><th scope="col">Secondary use / status</th></tr></thead><tbody>')
            for c in selected:
                parts.append('<tr>' + ''.join('<td>' + html.escape(str(v)) + '</td>' for v in [c['name'], c['hex'] + ' / ' + ', '.join(map(str, c['rgb'])), c['material'] + ' / ' + c['primary_usage'], c['secondary_usage'] + ' / ' + c['approval_status']]) + '</tr>')
            parts.append('</tbody></table></div></details>')
    if widget == 'chapters':
        groups = {}
        for page in art_pages(root):
            groups.setdefault(page['category'].split(' · ')[1], []).append(page)
        for group, pages in groups.items():
            if group == 'Start here':
                continue
            parts.append('<h3>' + html.escape(group) + '</h3><div class="chapter-grid">')
            for page in pages:
                parts.append(f'''<a href="{relative(path, page['path'])}"><strong>{html.escape(page['title'])}</strong><span>{html.escape(page['summary'])}</span></a>''')
            parts.append('</div>')
    if widget in {'scale-diagram', 'character-diagram'}:
        parts.append('''<div class="measure-diagram" role="img" aria-label="64 by 64 source canvas, 16 by 16 tile grid, approximately 32-pixel visible character. Contact at x32 y48. Visual root, ground footprint and collision are distinct."><div class="measured-cell"><img src="assets/character.png" width="64" height="64" alt="Registered original character study"><span class="measure-bounds"></span><span class="measure-contact"></span><span class="measure-footprint"></span><span class="measure-collision"></span></div><dl><dt>Canvas</dt><dd>64×64 native pixels</dd><dt>Tile grid</dt><dd>16×16, four cells across</dd><dt>Visible bounds</dt><dd>≈32 pixels tall; blue rectangle includes equipment</dd><dt>Ground contact / source pivot</dt><dd>(32,48), red marker</dd><dt>Example object footprint</dt><dd>16×8, dashed warm outline</dd><dt>Candidate collision</dt><dd>10×6 at contact, red rectangle; gameplay review required</dd><dt>Display scale</dt><dd>4× makes each native pixel 4×4 screen pixels</dd></dl></div><div class="scale-samples">''' + ''.join(f'<figure><img src="assets/tile-grass.png" width="{16 * scale}" height="{16 * scale}" alt="16 by 16 native tile shown at {scale} times"><figcaption>{scale}× · {16 * scale}×{16 * scale} display pixels</figcaption></figure>' for scale in [1,2,4,8]) + '</div>')
    if widget == 'animation':
        parts.append('''<div class="animation-viewer" data-animation><div class="art-controls"><button type="button" data-play>Play</button><button type="button" data-pause>Pause</button><button type="button" data-step="-1">Previous frame</button><button type="button" data-step="1">Next frame</button><label>Facing <select data-facing>''' + ''.join(f'<option value="{i}"'+(' selected' if d == 's' else '')+f'>{d.upper()}</option>' for i, d in enumerate(['n','ne','e','se','s','sw','w','nw'])) + '''</select></label><label>Speed <select data-speed><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="2">2×</option></select></label><label>Zoom <select data-animation-zoom><option value="1">1×</option><option value="2">2×</option><option value="4" selected>4×</option><option value="8">8×</option></select></label><label><input type="checkbox" data-animation-checker checked> Checkerboard</label><label><input type="checkbox" data-registration checked> Registration</label><label><input type="checkbox" data-animation-grid> Pixel grid</label><label><input type="checkbox" data-animation-tile-grid> 16-pixel grid</label></div><div class="pixel-scroll"><div class="animation-stage" style="--zoom:4"><canvas width="64" height="64" aria-label="Local original walk frames"></canvas><div class="registration-marker" aria-hidden="true"></div><div class="pixel-grid" aria-hidden="true"></div><div class="tile-grid" aria-hidden="true"></div></div></div><p data-frame-label role="status">Frame 1 of 6 · S · 100 ms</p><img class="animation-source" src="assets/character-walk.png" alt="Original eight-facing six-frame walk sheet; use Play to inspect" width="384" height="512"></div>''')
    if widget == 'gallery':
        for r in records:
            parts.append(f'<article class="reference-card" id="ref-{attr(r["id"])}"><h3>{html.escape(r["id"])}</h3><p><span class="art-label">{attr(r["status"])}</span> {r["dimensions"][0]}×{r["dimensions"][1]} · {attr(r["category"])} · {attr(r["palette"])}</p>')
            parts.append(viewer(r, path))
            parts.append('<p>' + html.escape(r['rules']) + '</p><details><summary>Source, attribution and local metadata</summary><dl>')
            for key in ['source', 'source_sha256', 'sha256', 'attribution']:
                parts.append(f'<dt>{attr(key)}</dt><dd>{html.escape(r[key])}</dd>')
            parts.append(f'</dl><a download href="{relative(path,r["path"])}">Download native PNG</a> · <a href="{relative(path,r["source"])}">Source file</a></details></article>')
    if widget == 'transition-masks':
        transition = by_id['transitions']
        parts.append('<details><summary>All 47 required masks and atlas coordinates</summary><div class="table-scroll" tabindex="0" role="region" aria-label="Transition patterns"><table><thead><tr><th scope="col">Mask</th><th scope="col">Bits N NE E SE S SW W NW</th><th scope="col">Column</th><th scope="col">Row within family</th></tr></thead><tbody>')
        for i, mask in enumerate(transition['masks']):
            parts.append(f'<tr><td>{mask}</td><td><code>{" ".join(str(int(bool(mask & (1 << n)))) for n in range(8))}</code></td><td>{i % 16}</td><td>{i // 16}</td></tr>')
        parts.append('</tbody></table></div></details>')
    if widget == 'templates':
        parts.append('<ul class="template-list">')
        for t in read(root, 'references')['templates']:
            parts.append(f'<li><a download href="{relative(path,t["path"])}">{Path(t["path"]).name}</a> — {t["validation"]}</li>')
        parts.append('</ul>')
    if widget == 'checklists':
        for name, entries in read(root, 'chapters')['checklists'].items():
            parts.append('<fieldset class="art-checklist"><legend>' + html.escape(name) + '</legend>')
            for i, entry in enumerate(entries):
                parts.append(f'<label><input type="checkbox" data-art-check="{attr(name)}-{i}"> {html.escape(entry)}</label>')
            parts.append('</fieldset>')
        parts.append('<button type="button" data-print>Print checklists</button><p>Checkmarks are temporary browser review aids; approval belongs in the delivery record.</p>')
    if widget == 'lighting':
        parts.append('''<div class="condition-viewer"><label>Condition <select data-condition>''' + ''.join(f'<option value="{v}">{v.title()}</option>' for v in ['day','dusk','night','rain','snow','torchlight']) + '''</select></label><img data-condition-image src="assets/light-day.png" width="384" height="256" alt="Same scene in day conditions"><label>Compare with day <input type="range" min="0" max="100" value="0" data-before-after aria-label="Day image overlay amount"></label><p data-condition-label role="status">Day · 0% day comparison</p></div>''')
    if widget == 'crowds':
        parts.append('<div class="crowd-viewer"><label>Actors <select data-crowd>' + ''.join(f'<option value="{c}">{c} actors</option>' for c in [1,2,5,12,30]) + '</select></label><img data-crowd-image src="assets/crowd-1.png" width="384" height="256" alt="Static readability study with one actor"></div>')
    if widget == 'ui-study':
        parts.append('''<div class="ui-study"><p class="eyebrow">Proposed interface study</p><h3>Field satchel</h3><div class="inventory-study" role="group" aria-label="Inspect sample inventory icons">''' + ''.join(f'<button type="button" data-item="{attr(name)}" aria-pressed="false"><span style="--icon-index:{i}" aria-hidden="true"></span><small>{name}</small></button>' for i, name in enumerate(['Sword','Tool','Potion','Food','Fish','Ore','Wood','Herb','Quest item','Currency'])) + '''</div><p data-item-detail role="status">Select an item to inspect its category silhouette.</p></div>''')
    return ''.join(parts)


def decorate_art_page(markup, page, root):
    if not page.get('art_bible'):
        return markup
    markup = markup.replace('</head>', '<link rel="stylesheet" href="../site/art-bible.css"><script defer src="../site/art-search-data.js"></script><script defer src="../site/art-bible.js"></script></head>')
    markup = markup.replace('<script defer src="../site/search-data.js"></script>', '')
    markup = markup.replace('<body data-root=', '<body class="art-bible" data-root=')
    markup = markup.replace('DEVELOPMENT GUIDE', 'OFFICIAL ART BIBLE')
    markup = markup.replace('Offline edition · 09 October 2026', 'Art Bible 0.1.0 · 15 October 2026')
    markup = markup.replace('Partial documentation. No game build.', 'New art: owner review pending.')
    start = markup.index('<nav aria-label="Main navigation">')
    end = markup.index('</nav>', start) + len('</nav>')
    nav = ['<nav aria-label="Art Bible navigation"><a href="../index.html">← Development guide</a>']
    current_group = None
    for p in art_pages(root):
        group = p['category'].split(' · ')[1]
        if group != current_group:
            nav.append('<span class="nav-group">' + html.escape(group) + '</span>')
            current_group = group
        nav.append(f'<a href="{relative(page["path"],p["path"])}"' + (' aria-current="page"' if p['path'] == page['path'] else '') + '>' + html.escape(p['title'].replace('Briarwake — Official Pixel Art Bible','Art Bible home')) + '</a>')
    nav.append('</nav>')
    markup = markup[:start] + ''.join(nav) + markup[end:]
    markup = markup.replace('<main id="main">', '<main id="main"><details class="art-search"><summary>Search the Art Bible</summary><label for="art-search">Search chapters, techniques and materials</label><input id="art-search" type="search" autocomplete="off"><p id="art-search-status" role="status">Search works locally, including offline.</p><ol id="art-search-results"></ol></details>')
    markup = markup.replace('<span aria-hidden="true"> / </span>', '<span aria-hidden="true"> / </span><a href="index.html">Art Bible</a><span aria-hidden="true"> / </span>', 1)
    pages = art_pages(root)
    position = next(i for i,p in enumerate(pages) if p['path'] == page['path'])
    related = '<nav class="art-related" aria-label="Chapter navigation">'
    if position:
        p = pages[position - 1]
        related += f'<a href="{relative(page["path"],p["path"])}">← {html.escape(p["title"])}</a>'
    if position + 1 < len(pages):
        p = pages[position + 1]
        related += f'<a href="{relative(page["path"],p["path"])}">{html.escape(p["title"])} →</a>'
    related += '</nav><p class="art-related">Related: ' + ' · '.join(f'<a href="{attr(slug)}.html">{html.escape(next(p["title"] for p in pages if p["path"] == "art-style/" + slug + ".html"))}</a>' for slug in page.get('related', [])) + ' · <a href="gallery.html">Reference gallery</a></p>'
    return markup.replace('<footer class="page-footer">', related + '<footer class="page-footer">')


def art_search_output(pages):
    return 'window.BRIARWAKE_ART_SEARCH = ' + json.dumps([{'path': p['path'].split('/')[-1], 'title': p['title'], 'summary': p['summary'], 'text': json.dumps(p['sections'], ensure_ascii=False)} for p in pages], ensure_ascii=False, separators=(',', ':')) + ';\n'
