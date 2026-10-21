"""Build canonical data contracts and their owned static documentation."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import posixpath
import re
from collections import Counter
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from typing import NamedTuple
from urllib.parse import unquote, urlsplit
from data_model import model_errors, schema_bundle, review_report, schema_children

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PAGE = 'guide/data-inventory.html'
ROADMAP_PAGE = 'guide/development-roadmap.html'
ROADMAP_EXCLUSION = ('Development planning, dependencies, acceptance criteria and implementation '
                     'progress; existing feature chapters retain canonical gameplay contracts.')
CATEGORIES = {'Enum': 'Enums', 'Interface': 'Interfaces', 'Schema': 'Schemas'}
DATA_START = '<!-- data-inventory:start -->'
DATA_END = '<!-- data-inventory:end -->'
DATA_BLOCK = re.compile(re.escape(DATA_START) + r'.*?' + re.escape(DATA_END), re.S)
ENTRY_KEYS = {'id', 'name', 'category', 'status', 'definition_status', 'canonical_page',
              'feature_pages', 'evidence', 'review_status', 'review_issues', 'definition',
              'responsibility', 'authority', 'modeling_notes', 'references', 'definition_extent',
              'reviewed_against', 'members', 'representation', 'previous_category'}
REGISTRY_KEYS = {'version', 'content_version', 'title', 'pages', 'reviewed_sources', 'scope_notes',
                 'review_issues', 'entries', 'schema_dialect', 'conventions', 'dependency_groups',
                 'shared_definitions', 'sample_bindings', 'initial_inventory_counts', 'audit_notes'}


class Document(HTMLParser):
    def __init__(self, source: str):
        super().__init__()
        self.ids = []
        self.headings = []
        self.main = False
        self.heading = None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if 'id' in values:
            self.ids.append(values['id'])
        if tag == 'main':
            self.main = True
        if self.main and tag in ('h1', 'h2', 'h3'):
            self.heading = [tag, values.get('id'), '']

    def handle_data(self, text):
        if self.heading is not None:
            self.heading[2] += text

    def handle_endtag(self, tag):
        if self.heading and tag == self.heading[0]:
            self.headings.append(tuple(self.heading))
            self.heading = None
        if tag == 'main':
            self.main = False


class DocumentMetadata(NamedTuple):
    ids: tuple
    headings: tuple


@lru_cache(maxsize=256)
def document_metadata(source):
    document = Document(source)
    return DocumentMetadata(tuple(document.ids), tuple(document.headings))


def load_registry(root=ROOT):
    return json.loads((root / 'sources/data-inventory.json').read_text(encoding='utf-8'))


def strip_data(source):
    return DATA_BLOCK.sub('', source)


def reviewed_content(source):
    main = re.search(r'<main\b.*?</main>', strip_data(source), re.S)
    if not main or '<footer' not in main.group():
        raise ValueError('Expected main content followed by a page footer')
    return main.group().split('<footer', 1)[0]


def content_fingerprint(source):
    return hashlib.sha256(reviewed_content(source).encode()).hexdigest()


def review_pages(registry, paths, root=ROOT, reference_pages=()):
    for path in dict.fromkeys(paths):
        target = (root / path).resolve()
        if not target.is_relative_to(root.resolve()) or not target.is_file() or target.suffix != '.html':
            raise ValueError('Review paths must be HTML files inside this repository')
        path = target.relative_to(root.resolve()).as_posix()
        if path == INVENTORY_PAGE:
            raise ValueError('The generated inventory page is not a feature source')
        source = target.read_text(encoding='utf-8')
        headings = Document(strip_data(source)).headings
        reviewed = next((p for p in registry['pages'] if p['page'] == path), None)
        if reviewed is None:
            reviewed = {'page': path, 'kind': 'Feature'}
            registry['pages'].append(reviewed)
        if path in reference_pages:
            reviewed.update(kind='Reference', exclusion_reason=ROADMAP_EXCLUSION)
        reviewed.update(title=next(title for tag, _, title in headings if tag == 'h1'),
                        review_status='Reviewed', reviewed_content_sha256=content_fingerprint(source),
                        reviewed_sections=[anchor for tag, anchor, _ in headings if tag != 'h1' and anchor])


def totals(registry):
    entries = registry['entries']
    return {
        **{plural.lower(): sum(e['category'] == category for e in entries)
           for category, plural in CATEGORIES.items()},
        'unique_structures': len(entries),
        'feature_pages_reviewed': sum(p['kind'] == 'Feature' for p in registry['pages']),
        'pages_reviewed': len(registry['pages']),
        'pages_with_data': len({p for e in entries for p in e['feature_pages']}),
        'existing': sum(e['status'] == 'Existing' for e in entries),
        'proposed': sum(e['status'] == 'Proposed' for e in entries),
        'needs_review': sum(e.get('review_status') == 'Needs Review' for e in entries),
        'partially_defined': sum(e['definition_extent'] == 'Partial' for e in entries),
        'open_review_items': sum(q['state'] == 'open' for q in registry['review_issues']),
        'resolved_review_items': sum(q['state'] == 'resolved' for q in registry['review_issues']),
        **{'fully_defined_' + plural.lower(): sum(e['category'] == category and
             e['definition_status'] == 'Fully Defined' for e in entries)
           for category, plural in CATEGORIES.items()},
    }


def validate_registry(registry, root=ROOT):
    errors = []
    if set(registry) != REGISTRY_KEYS:
        errors.append('Registry keys disagree with the canonical model format')
    if registry.get('version') != 2 or registry.get('title') != 'Data Inventory':
        errors.append('Unsupported registry version or title')
    if not isinstance(registry.get('content_version'), str) or not re.fullmatch(r'\d+\.\d+\.\d+-design', registry['content_version']):
        errors.append('Missing or invalid reviewed content version')
    catalog = json.loads((root / 'data/character_catalog.json').read_text(encoding='utf-8'))
    if catalog.get('version') != registry.get('content_version'):
        errors.append('Character catalog and canonical contract content versions disagree')
    entries = registry['entries']
    pages = registry['pages']
    documents = {p.relative_to(root).as_posix(): document_metadata(strip_data(p.read_text(encoding='utf-8')))
                 for p in sorted(root.rglob('*.html')) if p.relative_to(root).as_posix() != INVENTORY_PAGE}

    def unique(values, label):
        duplicates = [value for value, count in Counter(values).items() if count > 1]
        if duplicates:
            errors.append(f'Duplicate {label}: {duplicates}')

    def reference(ref, context):
        parsed = urlsplit(ref)
        target = root / unquote(parsed.path)
        if (parsed.scheme or parsed.netloc or not parsed.path or
                not target.resolve().is_relative_to(root.resolve()) or not target.is_file()):
            errors.append(f'{context}: missing or nonlocal reference {ref}')
        elif parsed.fragment:
            if parsed.path not in documents or unquote(parsed.fragment) not in documents[parsed.path].ids:
                errors.append(f'{context}: missing evidence anchor {ref}')

    unique((e['id'] for e in entries), 'inventory identifiers')
    unique((e['name'].casefold() for e in entries), 'inventory names')
    unique((p['page'] for p in pages), 'reviewed pages')
    unique((s['path'] for s in registry['reviewed_sources']), 'reviewed sources')
    page_by_path = {p['page']: p for p in pages}
    if set(page_by_path) != set(documents):
        errors.append(f'Coverage must review every source HTML page: {sorted(set(page_by_path) ^ set(documents))}')
    if set(CATEGORIES) != {e['category'] for e in entries}:
        errors.append('Inventory must contain exactly Enum, Interface and Schema categories')
    for page in pages:
        path = page['page']
        if page['kind'] not in ('Feature', 'Reference') or page['review_status'] != 'Reviewed':
            errors.append(f'{path}: missing page review classification')
        if path not in documents:
            continue
        source = (root / path).read_text(encoding='utf-8')
        if content_fingerprint(source) != page['reviewed_content_sha256']:
            errors.append(f'{path}: feature content changed; review coverage and update its fingerprint')
        headings = [anchor for tag, anchor, _ in documents[path].headings if tag != 'h1' and anchor]
        if headings != page['reviewed_sections']:
            errors.append(f'{path}: reviewed section list is stale')
        if any(title.strip() == 'Data' for _, _, title in documents[path].headings):
            errors.append(f'{path}: unmanaged Data section would be duplicated')
        if source.count(DATA_START) != source.count(DATA_END) or source.count(DATA_START) > 1:
            errors.append(f'{path}: malformed or duplicate generated Data blocks')
        referenced = any(path in e['feature_pages'] for e in entries)
        if referenced != (page['kind'] == 'Feature'):
            errors.append(f'{path}: feature coverage and Data associations disagree')
        if page['kind'] == 'Reference' and not page.get('exclusion_reason'):
            errors.append(f'{path}: excluded page needs a reason')
    names = {e['name'] for e in entries}
    issue_by_id = {issue['id']: issue for issue in registry['review_issues']}
    unique((issue['id'] for issue in registry['review_issues']), 'review issue identifiers')
    for issue in registry['review_issues']:
        if not re.fullmatch(r'[a-z][a-z0-9-]*', issue['id']):
            errors.append('Invalid review issue identifier')
        if not set(issue['entries']) <= names:
            errors.append(f"{issue['id']}: unknown reviewed entry")
        for ref in issue['references']:
            reference(ref, issue['id'])
    for entry in entries:
        label = entry['name']
        required_keys = ENTRY_KEYS - {'review_status', 'review_issues', 'members', 'representation', 'previous_category'}
        if set(entry) - ENTRY_KEYS or not required_keys <= set(entry):
            errors.append(f'{label}: invalid canonical entry metadata or missing definition')
        if not re.fullmatch(r'[a-z][a-z0-9-]*', entry['id']):
            errors.append(f'{label}: invalid stable identifier')
        if not re.fullmatch(r'[A-Z][A-Za-z0-9]*', label) and not (
                entry['status'] == 'Existing' and re.fullmatch(r'[a-z][a-z0-9_]*', label)):
            errors.append(f'{label}: proposed names must use PascalCase')
        if entry['status'] not in ('Existing', 'Proposed') or entry['definition_status'] not in ('Fully Defined', 'Needs Decision'):
            errors.append(f'{label}: invalid existence/definition status')
        if not entry['evidence'] or not entry['feature_pages']:
            errors.append(f'{label}: missing documentation evidence or feature associations')
        unique(entry['evidence'], f'evidence for {label}')
        unique(entry['feature_pages'], f'feature associations for {label}')
        for ref in entry['evidence']:
            reference(ref, label)
        if entry['canonical_page'] not in entry['evidence'] or '.html#' not in entry['canonical_page']:
            errors.append(f'{label}: canonical feature section must be an evidence reference')
        evidence_pages = {ref.split('#')[0] for ref in entry['evidence'] if '.html' in ref}
        if evidence_pages != set(entry['feature_pages']):
            errors.append(f'{label}: every feature association must have section evidence')
        for path in entry['feature_pages']:
            if path not in page_by_path or page_by_path[path]['kind'] != 'Feature':
                errors.append(f'{label}: missing or excluded feature page {path}')
        issue_ids = entry.get('review_issues', [])
        if bool(issue_ids) != (entry.get('review_status') == 'Needs Review'):
            errors.append(f'{label}: review status and issue references disagree')
        for identifier in issue_ids:
            if (identifier not in issue_by_id or label not in issue_by_id[identifier]['entries'] or
                    issue_by_id[identifier]['state'] != 'open'):
                errors.append(f'{label}: invalid review issue {identifier}')
        for identifier, issue in issue_by_id.items():
            if issue['state'] == 'open' and label in issue['entries'] and identifier not in issue_ids:
                errors.append(f'{label}: missing review issue backlink {identifier}')
    reviewed_sources = {s['path'] for s in registry['reviewed_sources']}
    evidence_files = {ref.split('#')[0] for e in entries for ref in e['evidence']}
    for source in registry['reviewed_sources']:
        reference(source['path'], 'Source review')
        if source['review_status'] != 'Reviewed':
            errors.append(f"Unreviewed source: {source['path']}")
    for path in sorted((root / 'data').glob('*.json')):
        rel = path.relative_to(root).as_posix()
        if rel not in reviewed_sources or rel not in evidence_files:
            errors.append(f'{rel}: existing structured data has no inventory/source review')
    ability_data = root / 'data/abilities.json'
    if ability_data.exists():
        for name in {a['request_schema'] for a in json.loads(ability_data.read_text())}:
            if name not in names:
                errors.append(f'Existing named request schema omitted: {name}')
    errors.extend(model_errors(registry, root))
    return errors


def escape(text):
    return html.escape(str(text), quote=True)


def relative_link(page, target, label):
    address, separator, anchor = target.partition('#')
    relative = posixpath.relpath(address, posixpath.dirname(page) or '.')
    href = relative + (separator + anchor if separator else '')
    return f'<a href="{escape(href)}">{escape(label)}</a>'


def entry_status(entry):
    text = entry['status'] + ' · ' + entry['definition_status']
    if entry.get('review_status'):
        text += ' · ' + entry['review_status']
    return escape(text)


def data_section(page, entries):
    lines = [DATA_START, '<section class="data-inventory" aria-labelledby="data">', '<h2 id="data">Data</h2>',
             '<p>Follow a type name to its canonical members, properties, constraints and review decisions. Definitions are generated from one shared registry.</p>']
    for category, plural in CATEGORIES.items():
        selected = sorted((e for e in entries if e['category'] == category), key=lambda e: e['name'].casefold())
        if selected:
            lines.extend([f'<h3 id="data-{plural.lower()}">{plural}</h3>', '<ul>'])
            for entry in selected:
                link = relative_link(page, INVENTORY_PAGE + '#' + entry['id'], entry['name'])
                lines.append(f'<li data-inventory-id="{entry["id"]}"><code>{link}</code> — {entry_status(entry)}</li>')
            lines.append('</ul>')
    return '\n'.join(lines + ['</section>', DATA_END])


def navigation(source, page):
    # Normalize shared navigation on every generated page.
    source = re.sub(r'(<a\b[^>]*href="(?:\.\./)?guide/networking\.html"[^>]*>).*?(</a>)',
                    lambda match: match.group(1) + 'Unreal C++ &amp; networking' + match.group(2),
                    source, count=1, flags=re.S)
    source = re.sub(r'<a data-inventory-nav\b[^>]*>.*?</a>', '', source, flags=re.S)
    current = ' aria-current="page"' if page == INVENTORY_PAGE else ''
    address = posixpath.relpath(INVENTORY_PAGE, posixpath.dirname(page) or '.')
    link = f'<a data-inventory-nav href="{address}"{current}>Data Inventory</a>'
    if source.count('<p>Catalogs</p>') != 1:
        raise ValueError(f'{page}: expected one Catalogs navigation group')
    source = source.replace('<p>Catalogs</p>', '<p>Catalogs</p>' + link)
    source = re.sub(r'<a data-roadmap-nav\b[^>]*>.*?</a>', '', source, flags=re.S)
    current = ' aria-current="page"' if page == ROADMAP_PAGE else (
        ' aria-current="location"' if page.startswith('guide/roadmap-') else '')
    address = posixpath.relpath(ROADMAP_PAGE, posixpath.dirname(page) or '.')
    link = f'<a data-roadmap-nav href="{address}"{current}>Development Roadmap</a>'
    source, count = re.subn(r'(<a class="nav-home\b[^>]*>.*?</a>)', r'\1' + link, source, flags=re.S)
    if count != 1:
        raise ValueError(f'{page}: expected one Overview navigation link')
    return source


def roadmap_search(root=ROOT):
    from build_development_roadmap import REFERENCE_PAGES, anchor_page, epic_page, phase_page, ticket_page

    roadmap = json.loads((root / 'sources/development-roadmap.json').read_text(encoding='utf-8'))
    records = [{'title': roadmap['title'], 'section': 'Development planning', 'url': ROADMAP_PAGE,
                'text': 'Dependency ordered epics acceptance criteria completion evidence phases milestones actionable progress'}]
    for phase in roadmap['phases']:
        records.append({'title': phase['title'], 'section': 'Development Roadmap · Phase',
                        'url': phase_page(phase) + '#' + phase['id'], 'text': phase['objective']})
    for epic in roadmap['epics']:
        records.append({'title': epic['id'] + ' · ' + epic['title'], 'section': 'Development Roadmap · Epic',
                        'url': epic_page(roadmap, epic['id']) + '#' + epic['id'],
                        'text': ' '.join([epic['objective'], epic['scope'], epic['status'],
                                          *epic['acceptance_criteria'], *epic['hard_dependencies'],
                                          *epic.get('recommended_predecessors', [])])})
        for number, criterion in enumerate(epic['acceptance_criteria'], 1):
            anchor = f'{epic["id"]}-AC-{number}'
            records.append({'title': f'{epic["id"]} · AC {number}',
                            'section': 'Development Roadmap · Acceptance criterion',
                            'url': epic_page(roadmap, epic['id']) + '#' + anchor,
                            'text': ' '.join([anchor, epic['title'], criterion])})
    for ticket in roadmap['tickets']:
        records.append({'title': ticket['id'] + ' · ' + ticket['title'], 'section': 'Development Roadmap · Ticket',
                        'url': ticket_page(ticket['id']) + '#' + ticket['id'],
                        'text': ' '.join([ticket['parent_epic'], ticket['status'], *ticket['epic_criteria'],
                                          *ticket['scope'], *ticket['acceptance_criteria'], *ticket['dependencies']])})
    for milestone in roadmap['milestones']:
        records.append({'title': milestone['title'], 'section': 'Development Roadmap · Milestone',
                        'url': anchor_page(roadmap, milestone['id']) + '#' + milestone['id'],
                        'text': ' '.join([milestone['objective'], milestone['outcome'], *milestone['required_epics']])})
    for decision in roadmap['sequencing_decisions']:
        records.append({'title': decision['title'], 'section': 'Development Roadmap · Sequencing decision',
                        'url': anchor_page(roadmap, decision['id']) + '#' + decision['id'],
                        'text': ' '.join([decision['choice'], decision['alternatives'], decision['basis'], *decision['epics']])})
    for decision in roadmap['open_decisions']:
        records.append({'title': decision['title'], 'section': 'Development Roadmap · Open decision',
                        'url': anchor_page(roadmap, decision['id']) + '#' + decision['id'],
                        'text': ' '.join([decision['description'], decision['resolution_gate'], *decision['epics']])})
    for anchor, title, text in [
        ('milestones', 'Major milestones', 'Playable outcomes required epics completion requirements'),
        ('sequencing-decisions', 'Architectural sequencing decisions', 'Authority replication prediction persistence alternatives'),
        ('coverage', 'Feature coverage and open decisions', 'Documented feature families deferred scope assumptions'),
        ('maintenance', 'Maintaining roadmap progress', 'Status updates completion evidence blockers rebuild validation'),
        ('audit', 'Roadmap Audit', 'Independent architectural review findings corrections readiness coverage dependencies decisions')]:
        records.append({'title': title, 'section': 'Development Roadmap · Reference',
                        'url': anchor_page(roadmap, anchor) + '#' + anchor, 'text': text})
    audit_page = REFERENCE_PAGES['audit'][0]
    audit_source = (root / audit_page).read_text(encoding='utf-8')
    for tag, anchor, title in Document(audit_source).headings:
        if tag == 'h3' and anchor and re.fullmatch(r'RA-\d{3}', anchor):
            section = re.search(r'<section aria-labelledby="' + re.escape(anchor) + r'">(.*?)</section>', audit_source, re.S)
            text = ' '.join(html.unescape(re.sub(r'<[^>]*>', ' ', section.group(1))).split())
            records.append({'title': title, 'section': 'Roadmap Audit · Finding',
                            'url': audit_page + '#' + anchor, 'text': text})
    return [dict(record, source='development-roadmap') for record in records]


def type_link(registry, name):
    entry = next((e for e in registry['entries'] if e['name'] == name), None)
    anchor = entry['id'] if entry else 'shared-' + name
    return relative_link(INVENTORY_PAGE, INVENTORY_PAGE + '#' + anchor, name)


def field_type(registry, schema):
    if '$ref' in schema:
        return type_link(registry, schema['$ref'].split('/')[-1])
    if 'anyOf' in schema:
        return ' | '.join(field_type(registry, branch) for branch in schema['anyOf'])
    if 'oneOf' in schema:
        return f'{len(schema["oneOf"])} explicit variants (see full schema)'
    if 'const' in schema:
        return '<code>' + escape(json.dumps(schema['const'])) + '</code>'
    kind = schema.get('type', 'composed')
    if kind == 'array':
        return ('set of ' if schema.get('uniqueItems') else 'array of ') + field_type(registry, schema['items'])
    if kind == 'object' and isinstance(schema.get('additionalProperties'), dict):
        return 'ID-keyed map of ' + field_type(registry, schema['additionalProperties'])
    return escape(kind)


def definition_html(registry, entry):
    schema = entry['definition']
    lines = ['<details class="definition"><summary>Inspect canonical definition</summary>',
             '<p>' + escape(schema['description']) + '</p>',
             '<p><strong>Responsibility:</strong> ' + escape(entry['responsibility']) +
             '<br><strong>Authority:</strong> ' + escape(entry['authority']) + '</p>']
    if entry.get('previous_category'):
        lines.append('<p>Reclassified from ' + escape(entry['previous_category']) + '; original name and anchor preserved.</p>')
    if entry['category'] == 'Enum':
        lines.append('<p>Representation: ' + escape(entry['representation']) +
                     '. Symbolic members have no assigned stored or wire value.</p><ul>')
        for member in entry['members']:
            value = ' = ' + escape(json.dumps(member['value'])) if 'value' in member else ''
            lines.append('<li><code>' + escape(member['id']) + value + '</code> — ' + escape(member['description']) + '</li>')
        lines.append('</ul>')
    if 'properties' in schema:
        lines.append('<div class="table-scroll"><table><thead><tr><th>Property</th><th>Type</th><th>Presence</th><th>Meaning / constraints</th></tr></thead><tbody>')
        for name, field in schema['properties'].items():
            bounds = {k: field[k] for k in ('minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum', 'multipleOf', 'minLength', 'maxLength', 'minItems', 'maxItems', 'enum', 'const') if k in field}
            identity = field.get('x-reference') or field.get('items', {}).get('x-reference')
            meaning = escape(field.get('description', ''))
            if identity:
                meaning += ' Reference: ' + type_link(registry, identity['target']) + ' (' + escape(identity['kind']) + ').'
            if bounds:
                meaning += ' <code>' + escape(json.dumps(bounds)) + '</code>'
            presence = 'Required' if name in schema['required'] else 'Optional (may be absent)'
            lines.append('<tr><td><code>' + escape(name) + '</code></td><td>' + field_type(registry, field) + '</td><td>' + presence + '</td><td>' + meaning + '</td></tr>')
        lines.append('</tbody></table></div>')
    elif '$ref' in schema:
        lines.append('<p>Uses ' + field_type(registry, schema) + ' directly.</p>')
    notes = [*schema.get('x-invariants', []), *entry['modeling_notes']]
    lines.append('<ul>' + ''.join('<li>' + escape(note) + '</li>' for note in notes) + '</ul>')
    if entry['references']:
        lines.append('<p>Related contracts: ' + ' · '.join(type_link(registry, name) for name in entry['references']) + '</p>')
    lines.append('<details><summary>Full machine-readable schema (includes nested shapes and nullability)</summary><pre><code>' + escape(json.dumps(schema, indent=2, ensure_ascii=False)) + '</code></pre></details></details>')
    return '\n'.join(lines)


def definition_search_text(schema):
    terms = [schema.get('description', ''), *schema.get('properties', {}), *schema.get('x-invariants', [])]
    terms.extend(str(value) for value in schema.get('enum', schema.get('x-members', [])))
    terms.extend(definition_search_text(child) for child in schema_children(schema))
    return ' '.join(terms)


def inventory_body(registry):
    page = INVENTORY_PAGE
    titles = {p['page']: p['title'] for p in registry['pages']}
    counts = totals(registry)
    body = ['<p class="lead">Canonical enums, interfaces and schemas, with explicit ownership, reusable definitions and source evidence.</p>',
            '<p>Reviewed content version: <code>' + escape(registry['content_version']) + '</code>. Registry format: 2.</p>',
            '<p>Fully Defined means the documentation contract is complete within its stated responsibility. Needs Decision identifies a partial contract with a recorded unresolved question. Neither status certifies runtime behavior or game balance. Existing/Proposed records provenance separately from completeness.</p>',
            '<p>' + relative_link(page, 'sources/data-inventory.json', 'Authoritative registry') + ' · ' + relative_link(page, 'sources/data-model.schema.json', 'Generated JSON Schema bundle') + ' · ' + relative_link(page, 'validation/data-model-review.txt', 'Complete review report') + ' · ' + relative_link(page, 'README.txt', 'Build and update instructions') + '</p>',
            '<div class="summary-strip">' + ''.join(f'<span class="badge">{counts[plural.lower()]} {plural}</span>' for plural in CATEGORIES.values()) + f'<span class="badge">{counts["unique_structures"]} unique structures</span><span class="badge">{counts["open_review_items"]} open design questions</span></div>']
    for category, plural in CATEGORIES.items():
        table_id = 'inventory-' + plural.lower()
        body.extend([f'<h2 id="{plural.lower()}">{plural}</h2>',
                     f'<div class="table-controls"><label>Filter {plural.lower()}<input type="search" data-filter="{table_id}" placeholder="Name, status or feature page"></label><span class="row-count" aria-live="polite"></span></div>',
                     f'<div class="table-scroll"><table id="{table_id}">',
                     '<thead><tr><th scope="col">Name</th><th scope="col">Status</th><th scope="col">Documentation references</th></tr></thead><tbody>'])
        for entry in sorted((e for e in registry['entries'] if e['category'] == category), key=lambda e: e['name'].casefold()):
            links = '<p>' + ' · '.join(relative_link(page, path + '#data', titles[path]) for path in entry['feature_pages']) + '</p>'
            evidence = '<details><summary>Source sections and existing formats</summary><ul>' + ''.join('<li>' + relative_link(page, ref, ref) + '</li>' for ref in entry['evidence']) + '</ul></details>'
            canonical = relative_link(page, entry['canonical_page'], 'Canonical feature section')
            issues = ''.join(' · ' + relative_link(page, page + '#review-' + issue, 'Review question') for issue in entry.get('review_issues', []))
            body.append(f'<tr id="{entry["id"]}"><td><code>{escape(entry["name"])}</code></td><td>{entry_status(entry)}{issues}</td><td>{definition_html(registry, entry)}{canonical}{links}{evidence}</td></tr>')
        body.append('</tbody></table></div>')
    body.extend(['<h2 id="coverage">Coverage</h2>', f'<p>{counts["feature_pages_reviewed"]} feature pages and {counts["pages_reviewed"]} source pages reviewed; {counts["pages_with_data"]} feature pages have Data sections. All {counts["unique_structures"]} original structures examined; {counts["partially_defined"]} remain partial / Needs Decision.</p>', '<ul>'])
    for plural in CATEGORIES.values():
        body.append(f'<li>{plural}: {counts[plural.lower()]} total, {counts["fully_defined_" + plural.lower()]} fully defined.</li>')
    body.extend('<li>' + escape(note) + '</li>' for note in registry['scope_notes'])
    body.extend(['</ul>', '<div class="table-scroll"><table><thead><tr><th scope="col">Reviewed page</th><th scope="col">Coverage</th></tr></thead><tbody>'])
    for reviewed in registry['pages']:
        count = sum(reviewed['page'] in e['feature_pages'] for e in registry['entries'])
        note = f'{count} associated structures' if count else reviewed['exclusion_reason']
        body.append('<tr><td>' + relative_link(page, reviewed['page'], reviewed['title']) + '</td><td>' + escape(note) + '</td></tr>')
    body.extend(['</tbody></table></div>', '<h2 id="conventions">Conventions and ownership</h2>', '<ul>'])
    body.extend('<li>' + escape(note) + '</li>' for note in registry['conventions'])
    body.append('</ul>')
    for group in registry['dependency_groups']:
        body.extend(['<h3>' + escape(group['name']) + '</h3>', '<p>' + escape(group['authority']) + '</p>',
                     '<p>' + ' · '.join(type_link(registry, name) for name in group['contracts']) + '</p>'])
    body.append('<h2 id="shared-definitions">Shared structural definitions</h2>')
    for name, schema in sorted(registry['shared_definitions'].items()):
        body.append('<details class="definition" id="shared-' + escape(name) + '"><summary>' + escape(name) + '</summary><p>' + escape(schema['description']) + '</p><pre><code>' + escape(json.dumps(schema, indent=2)) + '</code></pre></details>')
    body.extend(['<h2 id="needs-review">Decision history and future work</h2>', f'<p>{counts["open_review_items"]} open design questions; {counts["resolved_review_items"]} resolved. Resolved decisions retain their anchors and reasoning. Future Briarwake content, implementation and execution evidence are listed separately below; they do not claim completed game code.</p>'])
    for issue in registry['review_issues']:
        decision_label = 'Decision' if issue['state'] == 'resolved' else 'Recommendation'
        body.extend([f'<h3 id="review-{issue["id"]}">{escape(issue["id"].replace("-", " ").capitalize())} ({escape(issue["state"])})</h3>', '<p><strong>Review context:</strong> ' + escape(issue['question']) + '</p>',
                     '<p><strong>Alternatives:</strong> ' + escape(' / '.join(issue['alternatives'])) + '<br><strong>' + decision_label + ':</strong> ' + escape(issue['recommendation'] or 'No preference established.') + '<br><strong>Impact:</strong> ' + escape(issue['impact']) + '</p>',
                     '<p>' + ' · '.join(relative_link(page, page + '#' + next(e['id'] for e in registry['entries'] if e['name'] == name), name) for name in issue['entries']) + '</p>',
                     '<ul>' + ''.join('<li>' + relative_link(page, ref, ref) + '</li>' for ref in issue['references']) + '</ul>'])
        if issue.get('completion_criteria'):
            work_label = 'Future implementation work' if issue['state'] == 'resolved' else 'Required to resolve'
            body.append('<p><strong>' + work_label + ':</strong></p><ul>' + ''.join('<li>' + escape(item) + '</li>' for item in issue['completion_criteria']) + '</ul>')
    return '\n'.join(body)


def inventory_page(registry, template):
    prefix = template.split('<main', 1)[0]
    prefix = re.sub(r'<title>.*?</title>', '<title>Data Inventory · MMORPG Reference v2</title>', prefix)
    prefix = re.sub(r'<meta name="description"[^>]*>', '<meta name="description" content="Canonical data definitions, reviewed decisions and future Briarwake implementation work.">', prefix)
    prefix = re.sub(r' aria-current=(?:"page"|page)', '', prefix)
    prefix = prefix.replace('<span class="section-label">Engineering</span>', '<span class="section-label">Catalogs</span>')
    footer = re.search(r'<footer class="page-footer">.*?</footer>', template, re.S).group()
    toc = '<aside class="page-toc" aria-label="On this page"><p>ON THIS PAGE</p>' + ''.join(f'<a href="#{anchor}">{title}</a>' for anchor, title in [('enums','Enums'), ('interfaces','Interfaces'), ('schemas','Schemas'), ('coverage','Coverage'), ('conventions','Conventions'), ('shared-definitions','Shared definitions'), ('needs-review','Decisions and future work')]) + '</aside>'
    main = '<main id="main" tabindex="-1"><div class="breadcrumb"><a href="../index.html">Reference</a><span>/</span>Catalogs</div><h1>Data Inventory</h1><p class="page-description">Enums, interfaces and schemas; canonical definitions and review evidence.</p><div class="article-body">' + inventory_body(registry) + '</div>' + footer + '</main>'
    return navigation(prefix + main + toc + '</div></div></body></html>\n', INVENTORY_PAGE)


def expected_outputs(registry, root=ROOT):
    outputs = {}
    for reviewed in registry['pages']:
        page = reviewed['page']
        source = strip_data((root / page).read_text(encoding='utf-8'))
        entries = [e for e in registry['entries'] if page in e['feature_pages']]
        if entries:
            if source.count('</div><footer class="page-footer">') != 1:
                raise ValueError(f'{page}: expected one article/footer boundary')
            source = source.replace('</div><footer class="page-footer">', data_section(page, entries) + '</div><footer class="page-footer">')
        source = re.sub(r'<a data-inventory-toc\b[^>]*>.*?</a>', '', source, flags=re.S)
        if entries:
            source, count = re.subn(r'(<aside class="page-toc".*?)(</aside>)', r'\1<a data-inventory-toc href="#data">Data</a>\2', source, flags=re.S)
            if count != 1:
                raise ValueError(f'{page}: expected one page contents navigation')
        outputs[page] = navigation(source, page)
    outputs[INVENTORY_PAGE] = inventory_page(registry, (root / 'guide/networking.html').read_text(encoding='utf-8'))
    search_path = root / 'assets/search-index.js'
    search = json.loads(search_path.read_text(encoding='utf-8').removeprefix('window.SEARCH_INDEX=').strip().removesuffix(';'))
    search = [r for r in search if r.get('source') not in ('data-inventory', 'development-roadmap')]
    # Keep manually reviewed engineering search descriptions synchronized.
    refreshed_pages = {
        'index.html', 'guide/networking.html', 'guide/decisions.html',
        'guide/interface.html', 'guide/testing.html', 'guide/sources.html',
        'guide/execution.html',
    }
    for record in search:
        if record.get('source'):
            continue
        path, _, fragment = record['url'].partition('#')
        if path not in refreshed_pages:
            continue
        page_source = strip_data((root / path).read_text(encoding='utf-8'))
        main = re.search(r'<main\b.*?</main>', page_source, re.S)
        if not main:
            continue
        content = main.group()
        if fragment:
            heading = re.search(r'<h[1-6]\b[^>]*id="' + re.escape(fragment) + r'"[^>]*>', content)
            if heading:
                content = content[heading.start():]
                next_heading = re.search(r'<h[1-6]\b|<footer\b', content[len(heading.group()):])
                if next_heading:
                    content = content[:len(heading.group()) + next_heading.start()]
        plain = html.unescape(re.sub(r'<[^>]*>', ' ', content))
        record['text'] = ' '.join(plain.split())[:10000]
        if path == 'guide/networking.html':
            record['section'] = 'Unreal C++ & networking'
            if not fragment:
                record['title'] = 'Unreal C++ & networking'
    records = [{'title': 'Data Inventory', 'section': 'Catalogs', 'url': INVENTORY_PAGE, 'text': 'Enums interfaces schemas Fully Defined design decisions future Briarwake implementation work'}]
    for entry in sorted(registry['entries'], key=lambda e: e['name'].casefold()):
        records.append({'title': entry['name'], 'section': 'Data Inventory · ' + entry['category'], 'url': INVENTORY_PAGE + '#' + entry['id'],
                        'text': ' '.join([entry['status'], entry['definition_status'], entry.get('review_status', ''), definition_search_text(entry['definition']), *entry['references'], *entry['feature_pages'], *entry['evidence']])})
    for reviewed in registry['pages']:
        associated = [e['name'] for e in registry['entries'] if reviewed['page'] in e['feature_pages']]
        if associated:
            records.append({'title': reviewed['title'] + ' — Data', 'section': 'Data Inventory', 'url': reviewed['page'] + '#data', 'text': ' '.join(associated)})
    search.extend(dict(record, source='data-inventory') for record in records)
    search.extend(roadmap_search(root))
    outputs['assets/search-index.js'] = 'window.SEARCH_INDEX=' + json.dumps(search, ensure_ascii=True, separators=(',', ':')) + ';\n'
    manifest = json.loads((root / 'data/manifest.json').read_text(encoding='utf-8'))
    manifest.update(version=registry['content_version'], html_pages=len(registry['pages']) + 1,
                    guide_pages=sum(p['page'].startswith('guide/') for p in registry['pages']) + 1,
                    search_entries=len(search))
    outputs['data/manifest.json'] = json.dumps(manifest, indent=2) + '\n'
    outputs['sources/data-model.schema.json'] = json.dumps(schema_bundle(registry), indent=2, ensure_ascii=False) + '\n'
    outputs['validation/data-model-review.txt'] = review_report(registry)
    return outputs


def stale_outputs(outputs, root=ROOT):
    return [path for path, source in outputs.items()
            if not (root / path).exists() or (root / path).read_text(encoding='utf-8') != source]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check registry and generated output without writing')
    parser.add_argument('--review-page', action='append', default=[], metavar='PATH',
                        help='Record a completed manual feature review after updating its inventory associations')
    parser.add_argument('--review-roadmap', action='store_true',
                        help='Refresh all generated roadmap pages as planning references without gameplay associations')
    args = parser.parse_args()
    if args.check and (args.review_page or args.review_roadmap):
        parser.error('--check cannot update page reviews')
    registry = load_registry()
    roadmap_pages = []
    if args.review_roadmap:
        from build_development_roadmap import generated_page_paths

        roadmap = json.loads((ROOT / 'sources/development-roadmap.json').read_text(encoding='utf-8'))
        roadmap_pages = list(generated_page_paths(roadmap))
    try:
        review_pages(registry, [*args.review_page, *roadmap_pages], reference_pages=roadmap_pages)
    except ValueError as error:
        parser.error(str(error))
    if args.review_page or args.review_roadmap:
        registry['pages'].sort(key=lambda p: p['page'])
        registry_path = ROOT / 'sources/data-inventory.json'
        source = json.dumps(registry, indent=2, ensure_ascii=False) + '\n'
        if registry_path.read_text(encoding='utf-8') != source:
            registry_path.write_text(source, encoding='utf-8')
    errors = validate_registry(registry)
    if errors:
        raise SystemExit('\n'.join(errors))
    outputs = expected_outputs(registry)
    stale = stale_outputs(outputs)
    if args.check and stale:
        raise SystemExit('Stale generated inventory output: ' + ', '.join(stale))
    if not args.check:
        for path in stale:
            (ROOT / path).write_text(outputs[path], encoding='utf-8')
    print(json.dumps({'mode': 'check' if args.check else 'build', 'changed_files': 0 if args.check else len(stale), **totals(registry)}, indent=2))


if __name__ == '__main__':
    main()
