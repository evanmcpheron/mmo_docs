"""Render the offline roadmap from its sole editable planning registry."""
from __future__ import annotations

import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
import re

from build_data_inventory import navigation

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


def links(ids):
    return ', '.join(f'<a href="#{escape(i)}">{escape(i)}</a>' for i in ids) or 'None'


def doclinks(docs):
    return '; '.join(f'<a href="{escape("../" + d["href"], quote=True)}">{escape(d["label"])}</a>' for d in docs)


def bullets(items, ordered=False):
    tag = 'ol' if ordered else 'ul'
    return f'<{tag}>' + ''.join(f'<li>{escape(item)}</li>' for item in items) + f'</{tag}>'


def meter(value, label):
    return (f'<progress max="100" value="{value["percentage"]}" aria-label="{escape(label, quote=True)}"></progress>'
            f' <span>{value["complete"]}/{value["total"]} complete · {value["percentage"]:g}%</span>')


def render(data, root=ROOT):
    by_id = epic_map(data)
    parts = []

    def heading(anchor):
        title = dict(SECTIONS)[anchor]
        parts.append(f'<h2 id="{anchor}">{title}</h2>')

    heading('overview')
    parts.append(f'<p class="lead">{escape(data["purpose"])}</p>')
    parts.append('<div class="callout"><strong>Planning baseline, not implementation evidence.</strong><p>' +
                 escape(data['evidence_baseline']) + '</p></div>')
    for paragraph in data['reading_guide']:
        parts.append(f'<p>{escape(paragraph)}</p>')
    parts.append('<dl class="roadmap-terms">' + ''.join(
        f'<dt>{escape(term["label"])}</dt><dd>{escape(term["meaning"])}</dd>' for term in data['distinctions']) + '</dl>')
    parts.append('<p><strong>Analysis method.</strong> ' + escape(data['analysis_method']) + '</p>')
    parts.append('<p><strong>Research basis.</strong> ' + doclinks(data['research_docs']) +
                 '. The canonical registry and shipped catalogs were reviewed together with all class and profession pages. '
                 'Existing implementation-order recommendations were evaluated as hypotheses.</p>')

    heading('progress')
    all_progress = progress(data['epics'])
    metrics = [('Phases', len(data['phases'])), ('Epics', len(data['epics']))]
    metrics += [(s, all_progress['counts'][s]) for s in STATUSES]
    metrics += [('Overall completion', f'{all_progress["percentage"]:g}%'), ('Dependency-ready epics', len(ready_epics(data)))]
    parts.append('<div class="metrics roadmap-metrics">' + ''.join(
        f'<div><strong>{escape(str(value))}</strong><span>{escape(label)}</span></div>' for label, value in metrics) + '</div>')
    parts.append('<p>Completion counts verified epics equally; it is not an estimate of time, cost or remaining effort. '
                 'All counts, phase progress, milestone states and readiness below derive from the same Git-tracked '
                 '<a href="../sources/development-roadmap.json">roadmap registry</a>.</p>')
    ready = ready_epics(data)
    parts.append('<div class="callout"><strong>Currently actionable by hard prerequisites</strong>' +
                 (('<ul>' + ''.join(f'<li><a href="#{e["id"]}">{e["id"]} — {escape(e["title"])}</a>'
                                     f' <span class="badge">{escape(e["status"])}</span></li>' for e in ready) + '</ul>')
                  if ready else '<p>None. Review in-progress work, blocked epics and their prerequisite evidence.</p>') +
                 '<p>Readiness requires all hard prerequisites Complete and a Not Started or In Progress status. '
                 'It does not claim staffing, configuration decisions or external resources are already available. '
                 'A dependent Not Started epic is waiting on prerequisites; use Blocked only for an explicit recorded impediment.</p></div>')

    heading('sequence')
    parts.append('<p>Read top to bottom as the recommended integration sequence. Phases are review groups, not global start barriers: '
                 'work may advance whenever its own prerequisites are satisfied. Numbers in IDs are permanent identities, not scheduling positions.</p>')
    rows = []
    for phase in data['phases']:
        epics = [e for e in data['epics'] if e['phase'] == phase['id']]
        value = progress(epics)
        rows.append(f'<tr><td><a href="#{phase["id"]}">{escape(phase["title"])}</a></td>'
                    f'<td>{escape(phase["objective"])}</td><td>{len(epics)}</td>'
                    f'<td><a href="#{phase["milestone"]}">{escape(next(m["title"] for m in data["milestones"] if m["id"] == phase["milestone"]))}</a></td>'
                    f'<td>{meter(value, phase["title"])}<br>{escape(value["status"])}</td></tr>')
    parts.append('<div class="table-scroll"><table><caption>Complete recommended development sequence and phase progress</caption>'
                 '<thead><tr><th>Phase / detailed epics</th><th>Main objective</th><th>Epics</th><th>Completion milestone</th><th>Progress</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>')

    heading('epics')
    parts.append('<p>Every epic delivers one demonstrable capability. All members are required for their phase to be Complete. '
                 'A phase milestone can additionally require earlier prerequisites or an explicit integration epic; individual passes do not imply integration. '
                 'Epics in the same phase remain independently actionable when their own dependencies permit it. Disclosures are expanded for reading and printing.</p>')
    for phase in data['phases']:
        epics = [e for e in data['epics'] if e['phase'] == phase['id']]
        parts.append(f'<section class="roadmap-phase" aria-labelledby="{phase["id"]}"><h3 id="{phase["id"]}">{escape(phase["title"])}</h3>'
                     f'<p>{escape(phase["objective"])}</p><p><strong>Phase completion:</strong> All {len(epics)} epics below are Complete with verified AC evidence. '
                     f'{escape(phase["completion_condition"])}</p><p>{meter(progress(epics), phase["title"])}</p>')
        for epic in epics:
            identifier = epic['id']
            parts.append(f'<details open class="roadmap-epic" id="{identifier}"><summary><strong>{identifier} · {escape(epic["title"])}</strong> '
                         f'<span class="badge">{escape(epic["status"])}</span></summary><div class="roadmap-epic-body">')
            parts.append(f'<p><strong>Objective:</strong> {escape(epic["objective"])}</p><p><strong>Scope:</strong> {escape(epic["scope"])}</p>'
                         f'<p><strong>Hard dependencies:</strong> {links(epic["hard_dependencies"])}</p>'
                         f'<p><strong>Recommended predecessors:</strong> {links(epic["recommended_predecessors"])}</p>'
                         '<h4>Acceptance criteria (AC)</h4>' + bullets(epic['acceptance_criteria'], True) +
                         f'<p><strong>Completion evidence required:</strong> {escape(epic["completion_evidence"])}</p>')
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
            parts.append(f'<p><strong>Blockers:</strong> {escape("; ".join(epic["blockers"])) if epic["blockers"] else "None recorded; see hard prerequisites and linked open decisions."}</p>')
            if epic.get('ordering_rationale'):
                parts.append(f'<p><strong>Ordering rationale:</strong> {escape(epic["ordering_rationale"])}</p>')
            parts.append('<p><strong>Related documentation:</strong> ' + doclinks(epic['related_docs']) + '</p></div></details>')
        parts.append('</section>')

    heading('milestones')
    parts.append('<p>Requirements include the full hard-prerequisite closure shown below. Current states are derived, never edited separately. '
                 'The named integration/certification epic must pass on a common compatible build; completing components alone is insufficient.</p>')
    for milestone in data['milestones']:
        state = milestone_progress(data, milestone)
        parts.append(f'<section class="roadmap-milestone" aria-labelledby="{milestone["id"]}"><h3 id="{milestone["id"]}">{escape(milestone["title"])}</h3>'
                     f'<p><strong>Objective:</strong> {escape(milestone["objective"])}</p>'
                     f'<p><strong>Observable completion outcome:</strong> {escape(milestone["outcome"])}</p>'
                     f'<p><strong>Current status:</strong> {escape(state["status"])} · {meter(state, milestone["title"])}</p>'
                     f'<p><strong>Required epic IDs, including hard prerequisites:</strong> {links(prerequisite_closure(data, milestone["required_epics"]))}</p>'
                     f'<p><strong>Remaining required epic IDs:</strong> {links([i for i in prerequisite_closure(data, milestone["required_epics"]) if by_id[i]["status"] != "Complete"])}</p></section>')

    heading('sequencing-decisions')
    parts.append('<p>These are engineering judgments constrained by documented behavior. Alternatives remain reasonable where evidence is comparable; '
                 'a changed measurement may justify reordering without changing IDs.</p>')
    for decision in data['sequencing_decisions']:
        parts.append(f'<h3 id="{decision["id"]}">{escape(decision["title"])}</h3><p><strong>Chosen sequence:</strong> {escape(decision["choice"])}</p>'
                     f'<p><strong>Alternatives and tradeoff:</strong> {escape(decision["alternatives"])}</p>'
                     f'<p><strong>Basis:</strong> {escape(decision["basis"])}</p><p>{links(decision["epics"])} · {doclinks(decision["related_docs"])}</p>')
    parts.append('<p><strong>Independent technical checks.</strong> Official Godot documentation was checked on ' + escape(data['research_date']) +
                 ': <a href="https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_dedicated_servers.html">dedicated headless exports</a>, '
                 '<a href="https://docs.godotengine.org/en/stable/tutorials/networking/high_level_multiplayer.html">RPC authority and independent traffic channels</a>, and '
                 '<a href="https://docs.godotengine.org/en/stable/classes/class_multiplayersynchronizer.html">synchronizer visibility and unsupported Object/Resource values</a>. '
                 'These establish available building blocks, not an MMO architecture or a capacity guarantee. The early boundary proof is our inference from those limits and Briarwake’s requirements. '
                 'External references need internet; the roadmap itself does not.</p>')

    heading('coverage')
    parts.append('<div class="table-scroll"><table><caption>Documented feature families and their delivery path</caption><thead><tr><th>Feature family / requirements</th><th>Epics</th></tr></thead><tbody>' + ''.join(
        '<tr><td>' + escape(family['family']) + '<br>' + doclinks(family['related_docs']) + '</td><td>' + links(family['epics']) + '</td></tr>' for family in data['coverage']) + '</tbody></table></div>')
    parts.append('<h3 id="open-decisions">Open implementation decisions and assumptions</h3><p>All 29 recorded canonical contract questions are resolved in the current design revision. '
                 'The items below concern future implementation choices, authored content and evidence; they do not reopen settled design. '
                 'Each decision records a resolution gate so it cannot silently become a completed capability.</p>')
    for decision in data['open_decisions']:
        parts.append(f'<h4 id="{decision["id"]}">{escape(decision["title"])}</h4><p><strong>{escape(decision["kind"])}:</strong> {escape(decision["description"])}</p>'
                     f'<p><strong>Resolve by:</strong> {escape(decision["resolution_gate"])}</p><p>Affects {links(decision["epics"])} · {doclinks(decision["related_docs"])}</p>')
    parts.append('<h3 id="deferred-scope">Explicitly deferred or optional scope</h3>' + bullets(data['deferred_scope']))
    parts.append('<h3 id="critical-review">Final dependency review</h3>' + bullets(data['critical_review']))

    heading('maintenance')
    for paragraph in data['maintenance']:
        parts.append(f'<p>{escape(paragraph)}</p>')
    parts.append('<pre><code>python3 scripts/build_development_roadmap.py\npython3 scripts/build_data_inventory.py --review-page guide/development-roadmap.html\npython3 validation/check_development_roadmap.py\npython3 validation/run_checks.py</code></pre>')
    parts.append('<p>Commit the registry and generated outputs together. The inventory builder owns navigation/search/manifest outputs; '
                 'the roadmap builder owns this page body. Reading needs neither a build step nor JavaScript.</p>')
    main = ('<main id="main" tabindex="-1"><div class="breadcrumb"><a href="../index.html">Reference</a><span>/</span>Development planning</div>'
            '<h1>Briarwake Development Roadmap</h1><p class="page-description">Dependency-ordered capabilities, verification gates and Git-tracked progress from a blank project to the documented full game.</p>'
            '<div class="article-body">' + '\n'.join(parts) + '</div>'
            '<footer class="page-footer"><a href="../guide/audit.html">Readiness and open gates</a><span>Planning reference · evidence required for completion</span><a href="#main">Back to top ↑</a></footer></main>')
    template = (root / 'guide/networking.html').read_text(encoding='utf-8')
    template = re.sub(r'<title>.*?</title>', '<title>Briarwake Development Roadmap · MMORPG Reference v2</title>', template, count=1)
    template = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="The complete Briarwake capability roadmap, dependencies, acceptance evidence and development progress.">', template, count=1)
    template = template.replace('<link rel="stylesheet" href="../assets/styles.css">', '<link rel="stylesheet" href="../assets/styles.css"><link rel="stylesheet" href="../assets/roadmap.css">')
    template = re.sub(r'<span class="section-label">.*?</span>', '<span class="section-label">Development planning</span>', template, count=1)
    template = re.sub(r'<main\b.*?</main>', lambda _: main, template, count=1, flags=re.S)
    toc = '<aside class="page-toc" aria-label="On this page"><p>ON THIS PAGE</p>' + ''.join(
        f'<a href="#{anchor}">{escape(title)}</a>' for anchor, title in SECTIONS) + '</aside>'
    template = re.sub(r'<aside class="page-toc".*?</aside>', lambda _: toc, template, count=1, flags=re.S)
    template = re.sub(r'\saria-current(?:="page"|=page)', '', template)
    return navigation(template, PAGE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check generated HTML without writing it')
    args = parser.parse_args()
    data = load()
    import sys
    sys.path.insert(0, str(ROOT / 'validation'))
    from check_development_roadmap import roadmap_errors
    errors = roadmap_errors(data, check_generated=False)
    if errors:
        raise SystemExit('\n'.join(errors))
    expected = render(data)
    target = ROOT / PAGE
    if args.check:
        if not target.exists() or target.read_text(encoding='utf-8') != expected:
            raise SystemExit('Stale generated roadmap: ' + PAGE)
        print('Roadmap HTML is current.')
    else:
        target.write_text(expected, encoding='utf-8')
        print('Built ' + PAGE)


if __name__ == '__main__':
    main()
