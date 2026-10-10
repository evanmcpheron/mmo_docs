#!/usr/bin/env python3
"""Render the offline manual deterministically from its editable JSON registries."""
from __future__ import annotations
import argparse
import copy
import html
import json
import os
import re
from pathlib import Path
from urllib.parse import urlsplit
from faction_manual import faction_localization, faction_properties, faction_sections
ROOT = Path(__file__).resolve().parents[1]
NAVIGATION = [('index.html', 'Guide home'), ('getting-started.html', 'Start here'), ('development-roadmap.html', 'Phases 00–31'), ('first-vertical-slice.html', 'Vertical slices'), ('systems/index.html', 'System contracts'), ('professions/index.html', 'Five vocations'), ('world/authored-biomes.html', 'World and regions'), ('walkthroughs/index.html', 'Worked examples'), ('architecture.html', 'Architecture'), ('asset-index.html', 'Asset register'), ('dependency-map.html', 'Dependencies'), ('engineering/index.html', 'Engineering standard'), ('search.html', 'Search'), ('checklist.html', 'My phase progress'), ('feature-coverage.html', 'Coverage and gaps'), ('sources-verification.html', 'Sources and tests'), ('glossary.html', 'Glossary'), ('site-map.html', 'All pages')]

def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding='utf-8'))

def relative_link(current: str, target: str) -> str:
    if urlsplit(target).scheme or target.startswith('#'):
        return target
    destination, separator, fragment = target.partition('#')
    result = os.path.relpath(destination, os.path.dirname(current) or '.').replace(os.sep, '/')
    return result + (separator + fragment if separator else '')

def inline(text: str, current: str, assets: dict) -> str:
    """Escape authored text, allowing only explicit links and inline code."""
    tokens = re.split('(\\[\\[.*?\\]\\]|`[^`]+`)', str(text))
    rendered = []
    for token in tokens:
        if token.startswith('[[') and token.endswith(']]'):
            body = token[2:-2]
            if body.startswith('asset:'):
                name = body[6:]
                if name not in assets:
                    raise ValueError(f'{current}: unknown asset {name}')
                target = assets[name]['doc_path']
                label = name
            else:
                target, delimiter, label = body.partition('|')
                if not delimiter:
                    label = target
            external = bool(urlsplit(target).scheme)
            attributes = ' rel="noopener noreferrer"' if external else ''
            rendered.append(f'<a href="{html.escape(relative_link(current, target), quote=True)}"{attributes}>{html.escape(label)}</a>')
        elif token.startswith('`') and token.endswith('`'):
            rendered.append('<code>' + html.escape(token[1:-1]) + '</code>')
        else:
            rendered.append(html.escape(token))
    return ''.join(rendered)

def heading_id(title: str, number: int) -> str:
    return f'section-{number:02d}-' + re.sub('[^a-z0-9]+', '-', title.lower()).strip('-')

def make_table(table: dict, current: str, assets: dict, extra: str='') -> str:
    headers = ''.join(('<th scope="col">' + inline(cell_text, current, assets) + '</th>' for cell_text in table['headers']))
    rows = ''.join(('<tr>' + ''.join(('<td>' + inline(cell_text, current, assets) + '</td>' for cell_text in row)) + '</tr>' for row in table['rows']))
    return f'<div class="table-scroll" tabindex="0" role="region" aria-label="Scrollable reference table"><table {extra}><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table></div>'

def asset_identity(asset: dict) -> dict:
    return {'headers': ['Property', 'Value'], 'rows': [['Type', asset['type']], ['Parent / native base', asset['parent/native_base']], ['Planned physical path', asset['exact_game_path_or_source_path']], ['Content object path', asset.get('content_browser_path') or 'Not a Content Browser object'], ['Create / activate', f"{asset['first_phase']:02d} / {asset['first_active_phase']:02d}"], ['Work / status', asset['work_kind'] + ' / ' + asset['status']]]}

def prepare_page(source: dict, assets: dict, phases: list) -> dict:
    page = copy.deepcopy(source)
    if 'asset' in page:
        asset = assets[page['asset']]
        page['sections'][0]['table'] = asset_identity(asset)
        page['sections'][3]['table'] = {'headers': ['Field', 'Type / shape', 'Example / default', 'Exposure', 'Writer'], 'rows': faction_properties(asset, ROOT)}
        page['sections'][4]['paragraphs'][0] = asset['command']
        section = page['sections'][5]
        section['paragraphs'][0] = 'Creation prerequisites: ' + (', '.join((f'[[asset:{name}]]' for name in asset['dependencies'])) or 'None.')
        section['paragraphs'][1] = 'Direct registered reverse users: ' + (', '.join((f'[[asset:{name}]]' for name in asset['reverse_users'])) or 'None in the current creation graph.')
        section['paragraphs'][2] = 'Runtime consumers/assignments: ' + ', '.join(asset['consumers']) + '.'
    match = re.fullmatch('phases/phase-(\\d\\d)\\.html', page['path'])
    if match:
        phase = phases[int(match[1])]
        entries = [assets[name] for name in phase['creates']]
        page['sections'][2]['table']['rows'] = [[f"[[asset:{asset['name']}]]", asset['type'] + ' / ' + asset['parent/native_base'], asset['exact_game_path_or_source_path'], f"{asset['first_active_phase']:02d}"] for asset in entries] or [['No new registered identity', 'Extend existing consumers', 'See phase recipe', 'This phase']]
    if page.get('faction_source'):
        page['sections'].extend(faction_sections(page['faction_source'], ROOT))
    return page

def dynamic_content(page: dict, pages: list, assets: dict, phases: list) -> str:
    path = page['path']
    kind = page.get('dynamic')
    render = lambda text: inline(text, path, assets)
    if kind == 'home':
        counts = [('32', 'planned phases'), (str(len(assets)), 'asset contracts'), ('18', 'system chapters'), ('16', 'worked examples')]
        return '<div class="metrics">' + ''.join((f'<div><strong>{value}</strong><span>{label}</span></div>' for value, label in counts)) + '</div>'
    if kind == 'search':
        return '<div class="control-panel"><label for="search-input">Search words</label><input type="search" id="search-input" placeholder="Try fishing or lease epoch" autocomplete="off"><p id="search-status" role="status">Enter one or more words.</p><ol id="search-results" class="result-list"></ol></div>'
    if kind == 'assets':
        types = sorted({asset['type'] for asset in assets.values()})
        options = ''.join((f'<option>{html.escape(cell_text)}</option>' for cell_text in types))
        rows = []
        for asset in assets.values():
            rows.append(f'''<tr data-asset-row data-name="{html.escape(asset['name'].lower())}" data-type="{html.escape(asset['type'])}" data-status="{asset['status']}" data-phase="{asset['first_phase']}"><td>{render('[[asset:' + asset['name'] + ']]')}</td><td>{html.escape(asset['type'])}</td><td>{asset['first_phase']:02d} / {asset['first_active_phase']:02d}</td><td>{asset['status']}</td></tr>''')
        return f"""<div class="control-panel filters"><label>Name<input id="asset-query" type="search" placeholder="WatchFitting"></label><label>Type<select id="asset-type"><option value="">All types</option>{options}</select></label><label>Status<select id="asset-status"><option value="">All statuses</option><option>design</option><option>blocked</option><option>fixture</option></select></label><label>Creation phase<input id="asset-phase" type="number" min="0" max="31" placeholder="0–31"></label></div><p id="asset-count" role="status">{len(assets)} assets</p><div class="table-scroll" tabindex="0" role="region" aria-label="Filtered asset register"><table><thead><tr><th scope="col">Asset</th><th scope="col">Type</th><th scope="col">Create / activate</th><th scope="col">Status</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>"""
    if kind == 'dependencies':
        return make_table({'headers': ['Asset', 'Creation prerequisites', 'Registered reverse users'], 'rows': [[f"[[asset:{asset['name']}]]", ', '.join((f'[[asset:{name}]]' for name in asset['dependencies'])) or 'None', ', '.join((f'[[asset:{name}]]' for name in asset['reverse_users'])) or 'None'] for asset in assets.values()]}, path, assets)
    if kind == 'checklist':
        label_parts = []
        for phase in phases:
            number = phase['phase']
            url = relative_link(path, 'phases/phase-{:02d}.html'.format(number))
            label_parts.append(f'''<div class="check-row"><input type="checkbox" id="check-{number:02d}" data-phase-check="{number:02d}"><label for="check-{number:02d}">{number:02d} · {html.escape(phase['title'])}</label><a href="{url}">Read phase</a></div>''')
        labels = ''.join(label_parts)
        return '<div class="control-panel"><p id="progress-status" role="status"></p><div class="button-row"><button id="export-progress" type="button">Export progress JSON</button><label class="file-label">Import progress JSON<input id="import-progress" type="file" accept=".json,application/json"></label><button id="reset-progress" class="secondary" type="button">Reset checkmarks</button></div><p id="import-status" role="status"></p></div><div class="phase-checks">' + labels + '</div>'
    if kind == 'sitemap':
        categories = sorted({page['category'] for page in pages})
        return ''.join(('<section><h2>' + html.escape(category) + '</h2><ul class="link-grid">' + ''.join(('<li>' + render(f"[[{page['path']}|{page['title']}]]") + '</li>' for page in pages if page['category'] == category)) + '</ul></section>' for category in categories))
    return ''

def render_page(page: dict, pages: list, assets: dict, phases: list) -> str:
    path = page['path']
    parts = []
    toc = []
    for number, section in enumerate(page['sections'], 1):
        identifier = heading_id(section['title'], number)
        toc.append(f"""<li><a href="#{identifier}">{html.escape(section['title'])}</a></li>""")
        parts.append(f'''<section aria-labelledby="{identifier}"><h2 id="{identifier}">{html.escape(section['title'])}</h2>''')
        for paragraph in section.get('paragraphs', []):
            parts.append('<p>' + inline(paragraph, path, assets) + '</p>')
        for key, tag in [('steps', 'ol'), ('bullets', 'ul'), ('links', 'ul')]:
            if key in section:
                css = ' class="link-grid"' if key == 'links' else ''
                parts.append(f'<{tag}{css}>' + ''.join(('<li>' + inline(text, path, assets) + '</li>' for text in section[key])) + f'</{tag}>')
        if 'code' in section:
            parts.append('<pre><code>' + html.escape(section['code']) + '</code></pre>')
        if 'table' in section and page.get('dynamic') not in {'assets', 'dependencies'}:
            parts.append(make_table(section['table'], path, assets))
        parts.append('</section>')
    extra = dynamic_content(page, pages, assets, phases)
    body = '' + extra + ''.join(parts) if page.get('dynamic') == 'home' else ''.join(parts) + extra
    phase_match = re.fullmatch('phases/phase-(\\d\\d)\\.html', path)
    if phase_match:
        number = int(phase_match[1])
        footer = []
        if number:
            footer.append(inline(f'[[phases/phase-{number - 1:02d}.html|Previous phase]]', path, assets))
        footer.append(inline('[[checklist.html|Record local phase progress]]', path, assets))
        if number < 31:
            footer.append(inline(f'[[phases/phase-{number + 1:02d}.html|Next phase]]', path, assets))
        body += '<nav class="phase-navigation" aria-label="Phase navigation">' + ' '.join(footer) + '</nav>'
    root = relative_link(path, 'index.html').removesuffix('index.html') or './'
    navigation = ''.join((f'<a href="{relative_link(path, target)}"' + (' aria-current="page"' if target == path else '') + f'>{label}</a>' for target, label in NAVIGATION))
    title = html.escape(page['title'])
    category = html.escape(page['category'])
    summary = html.escape(page['summary'])
    return f'''<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="{html.escape(page['summary'], quote=True)}"><title>{title} · Briarwake</title><link rel="stylesheet" href="{root}site/style.css"><script defer src="{root}site/search-data.js"></script><script defer src="{root}site/app.js"></script></head>\n<body data-root="{root}"><a class="skip" href="#main">Skip to content</a><header class="mobile-bar"><a href="{root}index.html">Briarwake</a><button id="menu-toggle" type="button" aria-expanded="false" aria-controls="sidebar">Navigation</button></header>\n<aside id="sidebar" class="sidebar"><a class="brand" href="{root}index.html"><small>DEVELOPMENT GUIDE</small><strong>Briarwake</strong></a><p class="sidebar-description">Entirely 2D · Persistent world<br>Solo-capable · 1–30 test target</p><nav aria-label="Main navigation">{navigation}</nav><div class="sidebar-footer"><button id="theme-toggle" type="button">Change theme</button><p>Offline edition · 09 October 2026<br>Partial documentation. No game build.</p></div></aside>\n<div class="layout"><div class="breadcrumbs"><a href="{root}index.html">Guide</a><span aria-hidden="true"> / </span>{category}</div><main id="main"><header class="page-header"><p class="eyebrow">{category}</p><h1>{title}</h1><p class="lead">{summary}</p><p class="status-tag">{html.escape(page['maturity'])}</p></header>\n<details class="toc"><summary>On this page</summary><ol>{''.join(toc)}</ol></details>{body}\n<footer class="page-footer"><p>Planned game behavior is not runtime evidence. <a href="{root}sources-verification.html">Read sources and limitations</a>.</p><a href="#main">Back to top</a></footer></main></div></body></html>\n'''

def build_outputs() -> dict[str, str]:
    assets = {asset['name']: asset for asset in load_json('sources/current-asset-manifest.json')['assets']}
    phases = load_json('sources/phase-integration.json')['phases']
    pages = [prepare_page(page, assets, phases) for page in load_json('sources/manual-pages.json')['pages']]
    outputs = {page['path']: render_page(page, pages, assets, phases) for page in pages}
    search = []
    for page in pages:
        text = ' '.join((str(section.get(key, '')) for section in page['sections'] for key in ['title', 'paragraphs', 'steps', 'bullets', 'table']))
        search.append({'path': page['path'], 'title': page['title'], 'summary': page['summary'], 'category': page['category'], 'text': text})
    outputs['site/search-data.js'] = 'window.BRIARWAKE_SEARCH = ' + json.dumps(search, ensure_ascii=False, separators=(',', ':')) + ';\n'
    outputs['sources/faction-localization.en.json'] = json.dumps(faction_localization(ROOT), ensure_ascii=False, indent=2) + '\n'
    return outputs

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check generated files without changing them.')
    args = parser.parse_args()
    outputs = build_outputs()
    stale = []
    for relative, content in outputs.items():
        destination = ROOT / relative
        if args.check:
            if not destination.exists() or destination.read_text(encoding='utf-8') != content:
                stale.append(relative)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding='utf-8')
    if stale:
        print('FAIL: stale or missing generated files:\n' + '\n'.join(stale))
        return 1
    print(('PASS: generated files are current; ' if args.check else 'Built ') + f'{sum(path.endswith(".html") for path in outputs)} HTML pages, one offline search index and the faction English export.')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
