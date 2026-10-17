"""Render the offline roadmap from its sole editable planning registry."""
from __future__ import annotations

import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
import re

from build_data_inventory import Document, navigation

ROOT = Path(__file__).resolve().parents[1]
PAGE = 'guide/development-roadmap.html'
SOURCE = 'sources/development-roadmap.json'
STATUSES = ('Not Started', 'In Progress', 'Blocked', 'Complete')
SECTIONS = (
    ('overview', 'Development roadmap overview'),
    ('progress', 'Progress dashboard'),
    ('sequence', 'Recommended development sequence'),
    ('epics', 'Detailed epic roadmap'),
    ('milestones', 'Major milestones'),
    ('sequencing-decisions', 'Architectural sequencing decisions'),
    ('coverage', 'Feature coverage and open decisions'),
    ('maintenance', 'Updating progress'),
    ('audit', 'Roadmap Audit'),
)


def load(root=ROOT):
    return json.loads((root / SOURCE).read_text(encoding='utf-8'))


def epic_map(data):
    return {e['id']: e for e in data['epics']}


def prerequisite_closure(data, ids):
    by_id = epic_map(data)
    found = set()

    def visit(identifier):
        if identifier in found:
            return
        found.add(identifier)
        for dependency in by_id[identifier]['hard_dependencies']:
            visit(dependency)

    for identifier in ids:
        visit(identifier)
    return [e['id'] for e in data['epics'] if e['id'] in found]


def progress(epics):
    counts = Counter(e['status'] for e in epics)
    total = len(epics)
    complete = counts['Complete']
    status = ('Complete' if total and complete == total else
              'Blocked' if counts['Blocked'] else
              'In Progress' if counts['In Progress'] or complete else 'Not Started')
    return {'total': total, 'complete': complete, 'percentage': round(100 * complete / total, 1) if total else 0,
            'status': status, 'counts': {s: counts[s] for s in STATUSES}}


def ready_epics(data):
    by_id = epic_map(data)
    return [e for e in data['epics'] if e['status'] in ('Not Started', 'In Progress') and
            all(by_id[d]['status'] == 'Complete' for d in e['hard_dependencies'])]


def milestone_progress(data, milestone):
    by_id = epic_map(data)
    return progress([by_id[i] for i in prerequisite_closure(data, milestone['required_epics'])])


REFERENCE_PAGES = {
    'milestones': ('guide/roadmap-milestones.html', 'Milestones'),
    'sequencing-decisions': ('guide/roadmap-decisions.html', 'Sequencing decisions'),
    'coverage': ('guide/roadmap-coverage.html', 'Coverage and open decisions'),
    'maintenance': ('guide/roadmap-maintenance.html', 'Updating progress'),
    'audit': ('guide/roadmap-audit.html', 'Roadmap Audit'),
}


def phase_page(phase):
    identifier = phase['id'] if isinstance(phase, dict) else phase
    return 'guide/roadmap-' + identifier.removeprefix('phase-') + '.html'


def epic_page(data, identifier):
    return phase_page(epic_map(data)[identifier]['phase'])


def generated_page_paths(data):
    return [PAGE, *(phase_page(p) for p in data['phases']), *(p[0] for p in REFERENCE_PAGES.values())]


def anchor_page(data, identifier):
    if identifier in epic_map(data):
        return epic_page(data, identifier)
    if identifier in {p['id'] for p in data['phases']}:
        return phase_page(identifier)
    if identifier in {m['id'] for m in data['milestones']}:
        return REFERENCE_PAGES['milestones'][0]
    if identifier in {d['id'] for d in data['sequencing_decisions']} or identifier == 'critical-review':
        return REFERENCE_PAGES['sequencing-decisions'][0]
    if identifier in {d['id'] for d in data['open_decisions']} or identifier in ('open-decisions', 'deferred-scope'):
        return REFERENCE_PAGES['coverage'][0]
    return REFERENCE_PAGES.get(identifier, (PAGE, ''))[0]


def address(destination, page, anchor=None):
    from posixpath import dirname, relpath
    path = '' if destination == page and anchor else relpath(destination, dirname(page))
    return path + ('#' + anchor if anchor else '')


def link(destination, page, label, anchor=None, attributes=''):
    return f'<a href="{escape(address(destination, page, anchor), quote=True)}"{attributes}>{escape(label)}</a>'


def links(data, ids, page):
    return ', '.join(link(anchor_page(data, i), page, i, i) for i in ids) or 'None'


def doclinks(docs):
    return '; '.join(f'<a href="{escape("../" + d["href"], quote=True)}">{escape(d["label"])}</a>' for d in docs)


def bullets(items, ordered=False):
    tag = 'ol' if ordered else 'ul'
    return f'<{tag}>' + ''.join(f'<li>{escape(item)}</li>' for item in items) + f'</{tag}>'


def meter(value, label):
    return (f'<progress max="100" value="{value["percentage"]}" aria-label="{escape(label, quote=True)}"></progress>'
            f' <span>{value["complete"]}/{value["total"]} complete · {value["percentage"]:g}%</span>')


def roadmap_nav(data, page):
    destinations = [(PAGE, 'Dashboard'), *REFERENCE_PAGES.values()]
    items = [link(path, page, label, attributes=' aria-current="page"' if page == path else '')
             for path, label in destinations]
    phases = ''.join(link(phase_page(p), page, p['title'],
                          attributes=' aria-current="page"' if page == phase_page(p) else '') for p in data['phases'])
    return ('<nav class="roadmap-nav" aria-label="Development roadmap">' + ''.join(items) +
            '<details class="roadmap-phase-picker"><summary>All phases</summary><div>' + phases + '</div></details></nav>')


def phase_navigation(data, phase, page, position):
    index = next(i for i, p in enumerate(data['phases']) if p['id'] == phase['id'])
    previous = (link(phase_page(data['phases'][index - 1]), page, '← ' + data['phases'][index - 1]['title'])
                if index else link(PAGE, page, '← Roadmap dashboard'))
    following = (link(phase_page(data['phases'][index + 1]), page, data['phases'][index + 1]['title'] + ' →')
                 if index + 1 < len(data['phases']) else link(REFERENCE_PAGES['milestones'][0], page, 'Review milestones →'))
    return f'<nav class="roadmap-phase-nav" aria-label="Phase navigation ({position})">{previous}{following}</nav>'


def shell(data, page, title, description, body, toc, root=ROOT, phase=None):
    breadcrumb = '<a href="../index.html">Reference</a><span>/</span>'
    if page != PAGE:
        breadcrumb += link(PAGE, page, 'Development roadmap') + '<span>/</span>'
    breadcrumb += escape('Development roadmap' if page == PAGE else title)
    main = (f'<main id="main" tabindex="-1"><div class="breadcrumb">{breadcrumb}</div><h1>{escape(title)}</h1>'
            f'<p class="page-description">{escape(description)}</p><div class="article-body">{roadmap_nav(data, page)}' +
            ''.join(body) + '</div><footer class="page-footer">' + link(PAGE, page, 'Roadmap dashboard') +
            '<span>Planning reference · evidence required for completion</span><a href="#main">Back to top ↑</a></footer></main>')
    template = (root / 'guide/networking.html').read_text(encoding='utf-8')
    template = re.sub(r'\saria-current(?:="[^"]*"|=page)', '', template)
    template = re.sub(r'<title>.*?</title>', lambda _: f'<title>{escape(title)} · Briarwake Development Roadmap</title>', template, count=1)
    template = re.sub(r'<meta name="description" content="[^"]*">', lambda _: f'<meta name="description" content="{escape(description, quote=True)}">', template, count=1)
    template = template.replace('<link rel="stylesheet" href="../assets/styles.css">', '<link rel="stylesheet" href="../assets/styles.css"><link rel="stylesheet" href="../assets/roadmap.css">')
    template = re.sub(r'<span class="section-label">.*?</span>', '<span class="section-label">Development planning</span>', template, count=1)
    template = re.sub(r'<main\b.*?</main>', lambda _: main, template, count=1, flags=re.S)
    toc_html = '<aside class="page-toc" aria-label="On this page"><p>ON THIS PAGE</p>' + ''.join(
        f'<a href="#{escape(anchor)}">{escape(label)}</a>' for anchor, label in toc) + '</aside>'
    template = re.sub(r'<aside class="page-toc".*?</aside>', lambda _: toc_html, template, count=1, flags=re.S)
    return navigation(template, page)


def epic_content(data, epic, page):
    identifier = epic['id']
    parts = [f'<details open class="roadmap-epic" id="{identifier}"><summary><strong>{identifier} · {escape(epic["title"])}</strong> '
             f'<span class="badge">{escape(epic["status"])}</span></summary><div class="roadmap-epic-body">',
             f'<p><strong>Objective:</strong> {escape(epic["objective"])}</p><p><strong>Scope:</strong> {escape(epic["scope"])}</p>',
             f'<p><strong>Hard dependencies:</strong> {links(data, epic["hard_dependencies"], page)}</p>',
             f'<p><strong>Recommended predecessors:</strong> {links(data, epic["recommended_predecessors"], page)}</p>',
             '<h3>Acceptance criteria (AC)</h3>' + bullets(epic['acceptance_criteria'], True),
             f'<p><strong>Completion evidence required:</strong> {escape(epic["completion_evidence"])}</p>']
    if epic['verified_evidence']:
        parts.append('<p><strong>Recorded evidence:</strong></p><ul>')
        for evidence in epic['verified_evidence']:
            artifact = evidence['artifact']
            href = artifact if artifact.startswith('https://') else '../' + artifact
            parts.append(f'<li><a href="{escape(href, quote=True)}">{escape(evidence["summary"])}</a> — '
                         f'AC {escape(", ".join(map(str, evidence["criteria"])))}; {escape(evidence["result"])}; '
                         f'revision {escape(evidence["revision"])}</li>')
        parts.append('</ul>')
    else:
        parts.append('<p><strong>Recorded evidence:</strong> None. Required evidence above describes future verification.</p>')
    parts.append(f'<p><strong>Blockers:</strong> {escape("; ".join(epic["blockers"])) if epic["blockers"] else "None recorded; see hard prerequisites."}</p>')
    if epic.get('ordering_rationale'):
        parts.append(f'<p><strong>Ordering rationale:</strong> {escape(epic["ordering_rationale"])}</p>')
    decisions = [d for d in data['open_decisions'] if identifier in d['epics']]
    if decisions:
        parts.append('<p><strong>Related open decisions:</strong> ' + '; '.join(
            link(anchor_page(data, d['id']), page, d['title'], d['id']) for d in decisions) + '</p>')
    parts.append('<p><strong>Related documentation:</strong> ' + doclinks(epic['related_docs']) + '</p></div></details>')
    return ''.join(parts)


def render(data, root=ROOT):
    page = PAGE
    value = progress(data['epics'])
    parts = ['<h2 id="overview">Development roadmap overview</h2>', f'<p class="lead">{escape(data["purpose"])}</p>',
             '<p>Start with the next actionable epic below, or open a phase for its scope, dependencies, acceptance criteria and evidence. '
             'The order is an engineering recommendation; phases are review groups, and independent work can advance whenever its own hard prerequisites are met.</p>',
             '<h2 id="progress">Progress dashboard</h2>']
    metrics = [('Phases', len(data['phases'])), ('Epics', len(data['epics']))]
    metrics += [(s, value['counts'][s]) for s in STATUSES]
    metrics += [('Overall completion', f'{value["percentage"]:g}%'), ('Dependency-ready epics', len(ready_epics(data)))]
    parts.append('<div class="metrics roadmap-metrics">' + ''.join(
        f'<div><strong>{escape(str(number))}</strong><span>{escape(label)}</span></div>' for label, number in metrics) + '</div>')
    parts.append('<p>Counts, phase progress and milestone states share one ' +
                 '<a href="../sources/development-roadmap.json">Git-tracked registry</a>. Completion counts verified epics equally, not time or effort.</p>')
    ready = ready_epics(data)
    parts.append('<div class="callout"><strong>Currently actionable by hard prerequisites</strong>' +
                 ('<ul>' + ''.join('<li>' + link(epic_page(data, e['id']), page, e['id'] + ' — ' + e['title'], e['id']) +
                                  f' <span class="badge">{escape(e["status"])}</span></li>' for e in ready) + '</ul>'
                  if ready else '<p>None. Review in-progress work and recorded blockers.</p>') +
                 '<p>All hard prerequisites must be Complete. Readiness does not claim that staffing, configuration or external resources are available.</p></div>')
    parts.append('<h2 id="sequence">Recommended development sequence</h2><p id="epics">Choose a phase to read its detailed epics. '
                 'The ID links jump directly to an epic; IDs remain stable when scheduling changes.</p><div class="roadmap-phase-grid">')
    for phase in data['phases']:
        epics = [e for e in data['epics'] if e['phase'] == phase['id']]
        milestone = next(m for m in data['milestones'] if m['id'] == phase['milestone'])
        parts.append(f'<article class="roadmap-phase-card" id="{phase["id"]}"><h3>' + link(phase_page(phase), page, phase['title']) +
                     '</h3><p>' + escape(phase['objective']) + '</p><p>' + meter(progress(epics), phase['title']) +
                     f'<br><span class="badge">{escape(progress(epics)["status"])}</span></p><p><strong>Completion milestone:</strong> ' +
                     link(REFERENCE_PAGES['milestones'][0], page, milestone['title'], milestone['id'], f' id="{milestone["id"]}"') +
                     '</p><div class="roadmap-id-links" aria-label="Epic shortcuts">' + ''.join(
                         link(epic_page(data, e['id']), page, e['id'], e['id'],
                              f' id="{e["id"]}" class="roadmap-legacy-link" title="{escape(e["title"], quote=True)}"') for e in epics) +
                     '</div></article>')
    parts.append('</div><h2 id="reference">Roadmap reference</h2><div class="card-grid">')
    descriptions = {
        'milestones': 'See demonstrated outcomes, required epic IDs and what remains before each playable or release gate.',
        'sequencing-decisions': 'Read the dependency method, major alternatives and the reasons behind this sequence.',
        'coverage': 'Trace documented feature families to epics and review unresolved choices, assumptions and deferred scope.',
        'maintenance': 'Update statuses and completion evidence in the registry, then regenerate and validate the published pages.',
        'audit': 'Review the independent audit, applied corrections, per-epic assessment and outstanding decisions.',
    }
    for anchor, (destination, title) in REFERENCE_PAGES.items():
        parts.append(f'<a class="card" id="{anchor}" href="{escape(address(destination, page))}"><h3>{escape(title)}</h3>'
                     f'<p>{escape(descriptions[anchor])}</p><span>Open {escape(title.lower())} →</span></a>')
    parts.append('</div><details class="roadmap-reference-index"><summary>Decision shortcuts and existing section links</summary>')
    for group, heading in ((data['sequencing_decisions'], 'Sequencing decisions'), (data['open_decisions'], 'Open decisions')):
        parts.append(f'<h3>{heading}</h3><ul>')
        for decision in group:
            parts.append('<li>' + link(anchor_page(data, decision['id']), page, decision['title'], decision['id'], f' id="{decision["id"]}"') + '</li>')
        parts.append('</ul>')
    for identifier, title in (('open-decisions', 'All open decisions'), ('deferred-scope', 'Deferred or optional scope'), ('critical-review', 'Final dependency review')):
        parts.append('<p>' + link(anchor_page(data, identifier), page, title, identifier, f' id="{identifier}"') + '</p>')
    parts.append('</details>')
    return shell(data, page, data['title'], 'Development progress, actionable epics and a navigable sequence of phase guides.',
                 parts, [('overview', 'Overview'), ('progress', 'Progress'), ('sequence', 'Development phases'), ('reference', 'Roadmap reference')], root)


def render_phase(data, phase, root=ROOT):
    page = phase_page(phase)
    epics = [e for e in data['epics'] if e['phase'] == phase['id']]
    value = progress(epics)
    milestone = next(m for m in data['milestones'] if m['id'] == phase['milestone'])
    parts = [phase_navigation(data, phase, page, 'top'), f'<h2 id="{phase["id"]}">Phase objective and completion</h2>',
             f'<p>{escape(phase["objective"])}</p><p>{meter(value, phase["title"])}</p>',
             f'<p><strong>Phase status:</strong> {escape(value["status"])}. Complete only when all {len(epics)} epics below are Complete with verified evidence.</p>',
             f'<p>{escape(phase["completion_condition"])}</p><p><strong>Integrated completion milestone:</strong> ' +
             link(REFERENCE_PAGES['milestones'][0], page, milestone['title'], milestone['id']) +
             '. Its full prerequisites and integration evidence must also pass; individual components do not prove their integration.</p>',
             '<p>Hard dependencies are required for completion. Recommended predecessors are scheduling preferences. '
             'Other phases are not global start barriers. ' + link(REFERENCE_PAGES['sequencing-decisions'][0], page, 'How to read this roadmap', 'reading-guide') + '.</p>',
             '<h2 id="epic-index">Epics in this phase</h2><ol class="roadmap-contents">']
    ready_ids = {e['id'] for e in ready_epics(data)}
    for epic in epics:
        parts.append('<li>' + link(page, page, epic['id'] + ' · ' + epic['title'], epic['id']) +
                     f' <span class="badge">{escape(epic["status"])}</span>' +
                     (' <span class="badge success">Dependency-ready</span>' if epic['id'] in ready_ids else '') + '</li>')
    incoming = list(dict.fromkeys(dep for epic in epics for dep in epic['hard_dependencies'] if epic_map(data)[dep]['phase'] != phase['id']))
    parts.append('</ol><p><strong>Direct prerequisites from other phases:</strong> ' + links(data, incoming, page) +
                 '</p><h2 id="epics">Detailed epics</h2>')
    parts.extend(epic_content(data, epic, page) for epic in epics)
    parts.append(phase_navigation(data, phase, page, 'bottom'))
    return shell(data, page, phase['title'], phase['objective'], parts,
                 [(phase['id'], 'Objective and completion'), ('epic-index', 'Epic index')] + [(e['id'], e['id'] + ' · ' + e['title']) for e in epics], root, phase)


def render_milestones(data, root=ROOT):
    page = REFERENCE_PAGES['milestones'][0]
    by_id = epic_map(data)
    parts = ['<h2 id="milestones">Major milestones</h2><p>Each milestone is a demonstrated capability. Status and remaining work derive from the required epics and their hard prerequisites. '
             'An integration epic must pass on a compatible build; completed components alone are insufficient.</p>',
             '<ol class="roadmap-contents">' + ''.join('<li>' + link(page, page, m['title'], m['id']) +
                 f' <span class="badge">{escape(milestone_progress(data, m)["status"])}</span></li>' for m in data['milestones']) + '</ol>']
    for milestone in data['milestones']:
        state = milestone_progress(data, milestone)
        closure = prerequisite_closure(data, milestone['required_epics'])
        remaining = [i for i in closure if by_id[i]['status'] != 'Complete']
        parts.append(f'<section class="roadmap-milestone" aria-labelledby="{milestone["id"]}"><h2 id="{milestone["id"]}">{escape(milestone["title"])}</h2>'
                     f'<p><strong>Objective:</strong> {escape(milestone["objective"])}</p><p><strong>Observable completion outcome:</strong> {escape(milestone["outcome"])}</p>'
                     f'<p><strong>Current status:</strong> {escape(state["status"])} · {meter(state, milestone["title"])}</p>'
                     f'<p><strong>Required gates:</strong> {links(data, milestone["required_epics"], page)}</p>'
                     f'<details class="roadmap-prerequisites"><summary>Required epic IDs, including prerequisites ({len(closure)})</summary>'
                     f'<p>{links(data, closure, page)}</p></details><details class="roadmap-prerequisites"><summary>Remaining required epic IDs ({len(remaining)})</summary>'
                     f'<p>{links(data, remaining, page)}</p></details></section>')
    return shell(data, page, 'Roadmap milestones', 'Playable outcomes, completion requirements and remaining work across the Briarwake roadmap.',
                 parts, [(m['id'], m['title']) for m in data['milestones']], root)


def render_decisions(data, root=ROOT):
    page = REFERENCE_PAGES['sequencing-decisions'][0]
    parts = ['<h2 id="reading-guide">How to read the roadmap</h2>', '<div class="callout"><strong>Evidence baseline</strong><p>' + escape(data['evidence_baseline']) + '</p></div>']
    parts.extend(f'<p>{escape(paragraph)}</p>' for paragraph in data['reading_guide'])
    parts.append('<dl class="roadmap-terms">' + ''.join(f'<dt>{escape(t["label"])}</dt><dd>{escape(t["meaning"])}</dd>' for t in data['distinctions']) + '</dl>')
    parts.append('<h2 id="analysis">Dependency analysis and research</h2><p>' + escape(data['analysis_method']) + '</p><p><strong>Research basis:</strong> ' + doclinks(data['research_docs']) +
                 '. All class and profession pages, canonical structures and shipped catalogs were considered together; existing implementation-order advice was evaluated as a hypothesis.</p>')
    parts.append('<h2 id="sequencing-decisions">Architectural sequencing decisions</h2><p>These are engineering judgments constrained by documented behavior. '
                 'Where alternatives are comparable, changed evidence may justify a new order without changing IDs.</p>')
    for decision in data['sequencing_decisions']:
        parts.append(f'<section aria-labelledby="{decision["id"]}"><h3 id="{decision["id"]}">{escape(decision["title"])}</h3>'
                     f'<p><strong>Chosen sequence:</strong> {escape(decision["choice"])}</p><p><strong>Alternatives and tradeoff:</strong> {escape(decision["alternatives"])}</p>'
                     f'<p><strong>Basis:</strong> {escape(decision["basis"])}</p><p>{links(data, decision["epics"], page)} · {doclinks(decision["related_docs"])}</p></section>')
    parts.append('<p><strong>Independent technical checks.</strong> Official Godot documentation was checked on ' + escape(data['research_date']) +
                 ': <a href="https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_dedicated_servers.html">dedicated headless exports</a>, '
                 '<a href="https://docs.godotengine.org/en/stable/tutorials/networking/high_level_multiplayer.html">RPC authority and independent traffic channels</a>, and '
                 '<a href="https://docs.godotengine.org/en/stable/classes/class_multiplayersynchronizer.html">synchronizer visibility and unsupported Object/Resource values</a>. '
                 'These establish building blocks, not an MMO architecture or capacity guarantee. The early boundary proof is our inference from those limits and Briarwake’s requirements. '
                 'External references need internet; the roadmap pages do not.</p>')
    parts.append('<h2 id="critical-review">Final dependency review</h2>' + bullets(data['critical_review']))
    return shell(data, page, 'Roadmap sequencing decisions', 'The analysis method, important alternatives and architectural reasons behind the recommended development sequence.',
                 parts, [('reading-guide', 'How to read'), ('analysis', 'Analysis and research'), ('sequencing-decisions', 'Ordering decisions')] +
                 [(d['id'], d['title']) for d in data['sequencing_decisions']] + [('critical-review', 'Final dependency review')], root)


def render_coverage(data, root=ROOT):
    page = REFERENCE_PAGES['coverage'][0]
    parts = ['<h2 id="coverage">Feature coverage index</h2><div class="table-scroll"><table><caption>Documented feature families and their delivery path</caption>'
             '<thead><tr><th>Feature family / requirements</th><th>Epics</th></tr></thead><tbody>' + ''.join(
                 '<tr><td>' + escape(f['family']) + '<br>' + doclinks(f['related_docs']) + '</td><td>' + links(data, f['epics'], page) + '</td></tr>' for f in data['coverage']) + '</tbody></table></div>',
             '<h2 id="open-decisions">Open implementation decisions and assumptions</h2><p>All 29 recorded canonical contract questions are resolved in the current design revision. '
             'These items concern future implementation choices, authored content and evidence, with an explicit resolution gate.</p>']
    for decision in data['open_decisions']:
        parts.append(f'<section aria-labelledby="{decision["id"]}"><h3 id="{decision["id"]}">{escape(decision["title"])}</h3>'
                     f'<p><strong>{escape(decision["kind"])}:</strong> {escape(decision["description"])}</p><p><strong>Resolve by:</strong> {escape(decision["resolution_gate"])}</p>'
                     f'<p>Affects {links(data, decision["epics"], page)} · {doclinks(decision["related_docs"])}</p></section>')
    parts.append('<h2 id="deferred-scope">Explicitly deferred or optional scope</h2>' + bullets(data['deferred_scope']))
    return shell(data, page, 'Roadmap coverage and open decisions', 'Feature-to-epic traceability, unresolved implementation choices, assumptions and explicit scope boundaries.',
                 parts, [('coverage', 'Feature coverage'), ('open-decisions', 'Open decisions')] + [(d['id'], d['title']) for d in data['open_decisions']] + [('deferred-scope', 'Deferred scope')], root)


def render_maintenance(data, root=ROOT):
    page = REFERENCE_PAGES['maintenance'][0]
    parts = ['<h2 id="maintenance">Updating statuses and evidence</h2>']
    parts.extend(f'<p>{escape(paragraph)}</p>' for paragraph in data['maintenance'])
    parts.append('<h2 id="commands">Rebuild and validate</h2><pre><code>python3 scripts/build_development_roadmap.py\npython3 scripts/build_data_inventory.py --review-roadmap\npython3 validation/check_development_roadmap.py\npython3 validation/run_checks.py</code></pre>')
    parts.append('<p>Commit the registry and generated outputs together. The roadmap builder owns the dashboard, phase guides and reference pages; '
                 'the inventory builder owns shared navigation, search and manifest outputs. Reading requires neither a build step nor JavaScript.</p>')
    return shell(data, page, 'Updating roadmap progress', 'Maintain epic statuses, blockers and completion evidence without reorganizing the roadmap.',
                 parts, [('maintenance', 'Statuses and evidence'), ('commands', 'Rebuild and validate')], root)


def render_audit(data, root=ROOT):
    page = REFERENCE_PAGES['audit'][0]
    body = (root / 'sources/roadmap-audit.html.inc').read_text(encoding='utf-8')
    toc = [(anchor, title) for tag, anchor, title in Document('<main>' + body + '</main>').headings
           if tag == 'h2' and anchor]
    return shell(data, page, 'Roadmap Audit',
                 'Independent planning and architectural review, corrections, coverage and remaining decisions.',
                 [body], toc, root)


def generated_pages(data, root=ROOT):
    return {PAGE: render(data, root), **{phase_page(p): render_phase(data, p, root) for p in data['phases']},
            REFERENCE_PAGES['milestones'][0]: render_milestones(data, root),
            REFERENCE_PAGES['sequencing-decisions'][0]: render_decisions(data, root),
            REFERENCE_PAGES['coverage'][0]: render_coverage(data, root),
            REFERENCE_PAGES['maintenance'][0]: render_maintenance(data, root),
            REFERENCE_PAGES['audit'][0]: render_audit(data, root)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check all generated roadmap pages without writing')
    args = parser.parse_args()
    data = load()
    import sys
    sys.path.insert(0, str(ROOT / 'validation'))
    from check_development_roadmap import roadmap_errors
    errors = roadmap_errors(data, check_generated=False)
    if errors:
        raise SystemExit('\n'.join(errors))
    outputs = generated_pages(data)
    stale = [path for path, source in outputs.items() if not (ROOT / path).exists() or (ROOT / path).read_text(encoding='utf-8') != source]
    if args.check:
        if stale:
            raise SystemExit('Stale generated roadmap: ' + ', '.join(stale))
        print(f'All {len(outputs)} roadmap pages are current.')
    else:
        for path, source in outputs.items():
            (ROOT / path).write_text(source, encoding='utf-8')
        print(f'Built {len(outputs)} roadmap pages.')


if __name__ == '__main__':
    main()
