"""Check roadmap dependencies, evidence, coverage and generated progress."""
from __future__ import annotations

from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_development_roadmap import (PAGE, SECTIONS, STATUSES, address, anchor_page, generated_page_paths,
                                      generated_pages, load, phase_page, prerequisite_closure, progress, ticket_page)


class Anchors(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.ids = []
        self.references = []
        self.epic_ids = []
        self.link_targets = {}
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if 'id' in values:
            self.ids.append(values['id'])
        if tag == 'a' and 'href' in values:
            self.references.append(values['href'])
            if 'id' in values:
                self.link_targets[values['id']] = values['href']
        if 'roadmap-epic' in values.get('class', '').split():
            self.epic_ids.append(values.get('id'))


def roadmap_errors(data, root=ROOT, check_generated=True):
    errors = []
    required = {'version', 'title', 'research_date', 'purpose', 'evidence_baseline', 'reading_guide',
                'distinctions', 'analysis_method', 'research_docs', 'phases', 'epics', 'tickets', 'milestones',
                'sequencing_decisions', 'coverage', 'open_decisions', 'deferred_scope', 'critical_review', 'maintenance'}
    if not isinstance(data, dict) or set(data) != required:
        return ['Roadmap registry keys disagree with format 1']
    if data['version'] != 1 or data['title'] != 'Briarwake Development Roadmap':
        errors.append('Unsupported roadmap version or title')
    if not isinstance(data['tickets'], list):
        errors.append('tickets: expected a list')
    for key in ('phases', 'epics', 'milestones', 'coverage', 'sequencing_decisions', 'open_decisions',
                'reading_guide', 'distinctions', 'research_docs', 'deferred_scope', 'critical_review', 'maintenance'):
        if not isinstance(data[key], list) or not data[key]:
            errors.append(f'{key}: expected a nonempty list')
    if errors:
        return errors
    ids = [e.get('id') for e in data['epics']]
    phase_ids = [p.get('id') for p in data['phases']]
    milestone_ids = [m.get('id') for m in data['milestones']]
    anchors = ids + phase_ids + milestone_ids + [d.get('id') for d in data['sequencing_decisions'] + data['open_decisions']]
    anchors += [s[0] for s in SECTIONS] + ['open-decisions', 'deferred-scope', 'critical-review']
    if any(not isinstance(i, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9-]*', i) for i in anchors):
        return ['Every roadmap anchor must be a nonempty stable HTML identifier']
    if len(anchors) != len(set(anchors)):
        errors.append('Duplicate stable IDs/anchors')
    by_id = {e['id']: e for e in data['epics']}
    position = {i: n for n, i in enumerate(ids)}
    phase_position = {i: n for n, i in enumerate(phase_ids)}
    documents = {}

    def text(value, context):
        if not isinstance(value, str) or not value.strip():
            errors.append(f'{context}: expected nonempty text')

    def references(values, context):
        if not isinstance(values, list):
            errors.append(f'{context}: expected epic ID list')
            return
        if any(not isinstance(i, str) for i in values):
            errors.append(f'{context}: invalid epic ID')
            return
        if len(values) != len(set(values)):
            errors.append(f'{context}: duplicate epic reference')
        for identifier in values:
            if identifier not in by_id:
                errors.append(f'{context}: undefined epic {identifier}')

    def docs(values, context):
        if not isinstance(values, list) or not values:
            errors.append(f'{context}: documentation references required')
            return
        for reference in values:
            if not isinstance(reference, dict) or set(reference) != {'label', 'href'}:
                errors.append(f'{context}: expected labeled documentation link')
                continue
            text(reference['label'], context + ' label')
            href = reference['href']
            if not isinstance(href, str):
                errors.append(f'{context}: invalid documentation path')
                continue
            parsed = urlsplit(href)
            path = (root / unquote(parsed.path)).resolve()
            if parsed.scheme or parsed.netloc or not path.is_relative_to(root.resolve()) or not path.is_file():
                errors.append(f'{context}: missing/nonlocal documentation {href}')
            elif parsed.fragment:
                if path not in documents:
                    documents[path] = set(Anchors(path.read_text(encoding='utf-8')).ids)
                if unquote(parsed.fragment) not in documents[path]:
                    errors.append(f'{context}: missing documentation anchor {href}')

    epic_keys = {'id', 'phase', 'title', 'objective', 'scope', 'hard_dependencies', 'recommended_predecessors',
                 'acceptance_criteria', 'completion_evidence', 'related_docs', 'status', 'blockers',
                 'ordering_rationale', 'verified_evidence'}
    for epic in data['epics']:
        context = epic['id']
        if set(epic) != epic_keys:
            errors.append(f'{context}: epic fields disagree with format 1')
            continue
        if not re.fullmatch(r'BW-\d{3,}', context):
            errors.append(f'{context}: invalid epic ID')
        for field in ('title', 'objective', 'scope', 'completion_evidence'):
            text(epic[field], context + ' ' + field)
        if epic['phase'] not in phase_position:
            errors.append(f'{context}: undefined phase {epic["phase"]}')
        if epic['status'] not in STATUSES:
            errors.append(f'{context}: invalid status')
        criteria = epic['acceptance_criteria']
        if not isinstance(criteria, list) or len(criteria) < 3:
            errors.append(f'{context}: expected at least 3 acceptance criteria')
            criteria = []
        for criterion in criteria:
            text(criterion, context + ' AC')
        for field in ('hard_dependencies', 'recommended_predecessors'):
            references(epic[field], context + ' ' + field)
            for dependency in epic[field]:
                if dependency == context:
                    errors.append(f'{context}: self dependency')
                if dependency in position and position[dependency] >= position[context]:
                    errors.append(f'{context}: {field} conflicts with recommended sequence: {dependency}')
        if set(epic['hard_dependencies']) & set(epic['recommended_predecessors']):
            errors.append(f'{context}: same predecessor marked hard and recommended')
        if not isinstance(epic['blockers'], list) or any(not isinstance(b, str) or not b.strip() for b in epic['blockers']):
            errors.append(f'{context}: invalid blockers')
        if epic['status'] == 'Blocked' and not epic['blockers']:
            errors.append(f'{context}: Blocked requires an explicit blocker')
        if epic['status'] == 'Complete' and epic['blockers']:
            errors.append(f'{context}: Complete cannot retain blockers')
        evidence = epic['verified_evidence']
        covered = set()
        if not isinstance(evidence, list):
            errors.append(f'{context}: verified_evidence must be a list')
            evidence = []
        for record in evidence:
            if not isinstance(record, dict) or set(record) != {'criteria', 'artifact', 'revision', 'result', 'summary'}:
                errors.append(f'{context}: invalid evidence record')
                continue
            for field in ('artifact', 'revision', 'summary'):
                text(record[field], context + ' evidence ' + field)
            if record['result'] not in ('Passed', 'Failed'):
                errors.append(f'{context}: evidence result must be Passed or Failed')
            numbers = record['criteria']
            if (not isinstance(numbers, list) or not numbers or
                    any(type(n) is not int or not 1 <= n <= len(criteria) for n in numbers)):
                errors.append(f'{context}: evidence must identify existing AC numbers')
            elif record['result'] == 'Passed':
                covered.update(numbers)
            if record['result'] == 'Failed' and epic['status'] == 'Complete':
                errors.append(f'{context}: Complete cannot retain failing current evidence')
            artifact = record['artifact']
            if isinstance(artifact, str):
                parsed = urlsplit(artifact)
                if parsed.scheme:
                    if parsed.scheme != 'https' or not parsed.netloc:
                        errors.append(f'{context}: evidence must use a local path or HTTPS URL')
                else:
                    path = (root / unquote(parsed.path)).resolve()
                    if not path.is_relative_to(root.resolve()) or not path.is_file():
                        errors.append(f'{context}: missing evidence artifact {artifact}')
        if epic['status'] == 'Complete':
            if covered != set(range(1, len(criteria) + 1)):
                errors.append(f'{context}: Complete requires passing evidence for every AC')
            if any(by_id[d]['status'] != 'Complete' for d in epic['hard_dependencies'] if d in by_id):
                errors.append(f'{context}: Complete requires complete hard prerequisites')
        docs(epic['related_docs'], context)

    ticket_keys = {'id', 'parent_epic', 'title', 'scope', 'out_of_scope', 'dependencies', 'epic_criteria',
                   'acceptance_criteria', 'manual_test', 'completion_evidence', 'related_docs', 'status',
                   'blockers', 'verified_evidence'}
    tickets = data['tickets']
    if any(not isinstance(t, dict) or set(t) != ticket_keys for t in tickets):
        errors.append('Ticket fields disagree with format 1')
        return errors
    ticket_ids = [t['id'] for t in tickets]
    if any(not isinstance(i, str) or not re.fullmatch(r'BW-\d{3,}-T\d{2,}', i) for i in ticket_ids):
        errors.append('Invalid stable ticket ID')
        return errors
    if len(set(anchors + ticket_ids)) != len(anchors + ticket_ids):
        errors.append('Duplicate stable IDs/anchors including tickets')
    ticket_by_id = {t['id']: t for t in tickets}
    ticket_position = {i: n for n, i in enumerate(ticket_ids)}
    coverage = {}
    for ticket in tickets:
        context = ticket['id']
        parent = ticket['parent_epic']
        if not isinstance(parent, str) or parent not in by_id or not context.startswith(parent + '-T'):
            errors.append(f'{context}: invalid parent epic')
            continue
        for field in ('title', 'completion_evidence'):
            text(ticket[field], context + ' ' + field)
        for field in ('scope', 'out_of_scope', 'epic_criteria', 'acceptance_criteria'):
            values = ticket[field]
            if not isinstance(values, list) or not values or any(not isinstance(v, str) or not v.strip() for v in values):
                errors.append(f'{context}: {field} requires nonempty text entries')
        valid_criteria = {f'{parent}-AC-{n}' for n in range(1, len(by_id[parent]['acceptance_criteria']) + 1)}
        criteria = ticket['epic_criteria']
        if isinstance(criteria, list) and all(isinstance(c, str) for c in criteria):
            if len(criteria) != len(set(criteria)) or set(criteria) - valid_criteria:
                errors.append(f'{context}: epic criteria must be unique exact parent AC anchors')
            coverage.setdefault(parent, set()).update(criteria)
        dependencies = ticket['dependencies']
        if not isinstance(dependencies, list) or any(not isinstance(d, str) for d in dependencies):
            errors.append(f'{context}: expected dependency ID list')
            dependencies = []
        if len(dependencies) != len(set(dependencies)):
            errors.append(f'{context}: duplicate dependency')
        for dependency in dependencies:
            if dependency not in by_id and dependency not in ticket_by_id:
                errors.append(f'{context}: undefined dependency {dependency}')
            elif dependency == parent:
                errors.append(f'{context}: cannot depend on its own parent epic')
            elif dependency in ticket_position and ticket_position[dependency] >= ticket_position[context]:
                errors.append(f'{context}: ticket dependency conflicts with execution order: {dependency}')
        test = ticket['manual_test']
        if not isinstance(test, dict):
            errors.append(f'{context}: manual test must be an object')
        elif set(test) == {'not_applicable'}:
            text(test['not_applicable'], context + ' manual test rationale')
        elif set(test) == {'launch', 'setup', 'actions', 'expected_results', 'reset'}:
            text(test['launch'], context + ' manual launch')
            for field in ('setup', 'actions', 'expected_results', 'reset'):
                values = test[field]
                if not isinstance(values, list) or not values or any(not isinstance(v, str) or not v.strip() for v in values):
                    errors.append(f'{context}: manual test {field} requires nonempty steps')
        else:
            errors.append(f'{context}: manual test needs launch, setup, actions, expected results and reset, or a rationale')
        if ticket['status'] not in STATUSES:
            errors.append(f'{context}: invalid status')
        blockers = ticket['blockers']
        if not isinstance(blockers, list) or any(not isinstance(b, str) or not b.strip() for b in blockers):
            errors.append(f'{context}: invalid blockers')
        if ticket['status'] == 'Blocked' and not blockers:
            errors.append(f'{context}: Blocked requires an explicit blocker')
        evidence = ticket['verified_evidence']
        passed = set()
        failed = False
        if not isinstance(evidence, list):
            errors.append(f'{context}: verified_evidence must be a list')
            evidence = []
        for record in evidence:
            if not isinstance(record, dict) or set(record) != {'criteria', 'artifact', 'revision', 'result', 'summary'}:
                errors.append(f'{context}: invalid evidence record')
                continue
            for field in ('artifact', 'revision', 'summary'):
                text(record[field], context + ' evidence ' + field)
            if record['result'] not in ('Passed', 'Failed'):
                errors.append(f'{context}: evidence result must be Passed or Failed')
            numbers = record['criteria']
            if (not isinstance(numbers, list) or not numbers or any(type(n) is not int or
                    not 1 <= n <= len(ticket['acceptance_criteria']) for n in numbers)):
                errors.append(f'{context}: evidence must identify existing ticket AC numbers')
            elif record['result'] == 'Passed':
                passed.update(numbers)
            failed |= record['result'] == 'Failed'
            artifact = record['artifact']
            if isinstance(artifact, str):
                parsed = urlsplit(artifact)
                path = (root / unquote(parsed.path)).resolve()
                if parsed.scheme:
                    if parsed.scheme != 'https' or not parsed.netloc:
                        errors.append(f'{context}: evidence must use a local path or HTTPS URL')
                elif not path.is_relative_to(root.resolve()) or not path.is_file():
                    errors.append(f'{context}: missing evidence artifact {artifact}')
        if ticket['status'] == 'Complete':
            if blockers or failed or passed != set(range(1, len(ticket['acceptance_criteria']) + 1)):
                errors.append(f'{context}: Complete requires passing evidence for every AC and no blockers or failures')
            if any((ticket_by_id.get(d) or by_id.get(d) or {}).get('status') != 'Complete' for d in dependencies):
                errors.append(f'{context}: Complete requires complete dependencies')
        docs(ticket['related_docs'], context)
    for parent in {t['parent_epic'] for t in tickets if isinstance(t['parent_epic'], str) and t['parent_epic'] in by_id}:
        expected = {f'{parent}-AC-{n}' for n in range(1, len(by_id[parent]['acceptance_criteria']) + 1)}
        if coverage.get(parent, set()) != expected:
            errors.append(f'{parent}: tickets must cover every epic acceptance criterion')

    colors = {}
    def visit(identifier, trail):
        if colors.get(identifier) == 'visiting':
            errors.append('Hard dependency cycle: ' + ' -> '.join(trail + [identifier]))
            return
        if colors.get(identifier) == 'done':
            return
        colors[identifier] = 'visiting'
        for dependency in by_id[identifier].get('hard_dependencies', []):
            if dependency in by_id:
                visit(dependency, trail + [identifier])
        colors[identifier] = 'done'
    for identifier in by_id:
        visit(identifier, [])

    for phase in data['phases']:
        if set(phase) != {'id', 'title', 'objective', 'milestone', 'completion_condition'}:
            errors.append(f'{phase["id"]}: invalid phase fields')
            continue
        for field in ('title', 'objective', 'completion_condition'):
            text(phase[field], phase['id'] + ' ' + field)
        if phase['milestone'] not in milestone_ids:
            errors.append(f'{phase["id"]}: undefined phase milestone')
        if not any(e.get('phase') == phase['id'] for e in data['epics']):
            errors.append(f'{phase["id"]}: empty phase')
    phase_order = [phase_position[e['phase']] for e in data['epics'] if e.get('phase') in phase_position]
    if phase_order != sorted(phase_order):
        errors.append('Epic sequence must be grouped in recommended phase order')
    for milestone in data['milestones']:
        if set(milestone) != {'id', 'title', 'objective', 'required_epics', 'outcome'}:
            errors.append(f'{milestone["id"]}: invalid milestone fields; status must be derived')
            continue
        for field in ('title', 'objective', 'outcome'):
            text(milestone[field], milestone['id'] + ' ' + field)
        references(milestone['required_epics'], milestone['id'])
        if not milestone['required_epics']:
            errors.append(f'{milestone["id"]}: empty milestone')
    covered = set()
    source_pages = set()
    for family in data['coverage']:
        text(family.get('family'), 'Coverage family')
        references(family.get('epics'), 'Coverage ' + str(family.get('family')))
        covered.update(family.get('epics', []))
        docs(family.get('related_docs'), 'Coverage ' + str(family.get('family')))
    if set(ids) - covered:
        errors.append('Epics absent from feature coverage: ' + ', '.join(sorted(set(ids) - covered)))
    for row in data['coverage'] + data['epics']:
        source_pages.update(urlsplit(d['href']).path for d in row.get('related_docs', []))
    registry_path = root / 'sources/data-inventory.json'
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding='utf-8'))
        missing = {p['page'] for p in registry['pages'] if p['kind'] == 'Feature'} - source_pages
        if missing:
            errors.append('Feature pages without roadmap traceability: ' + ', '.join(sorted(missing)))
    for row in data['sequencing_decisions'] + data['open_decisions']:
        references(row.get('epics'), row['id'])
        docs(row.get('related_docs'), row['id'])
    docs(data['research_docs'], 'Research basis')
    if not errors:
        for phase in data['phases']:
            milestone = next(m for m in data['milestones'] if m['id'] == phase['milestone'])
            closure = set(prerequisite_closure(data, milestone['required_epics']))
            members = {e['id'] for e in data['epics'] if e['phase'] == phase['id']}
            if members - closure:
                errors.append(f'{phase["id"]}: phase milestone omits required member epics')
        if set(prerequisite_closure(data, data['milestones'][-1]['required_epics'])) != set(ids):
            errors.append('Final full-game milestone must account for every epic')
    if not errors and len(generated_page_paths(data)) != len(set(generated_page_paths(data))):
        errors.append('Generated roadmap page paths must be unique')
    if check_generated and not errors:
        outputs = generated_pages(data, root)
        parsed = {path: Anchors(source) for path, source in outputs.items()}
        for path, expected in outputs.items():
            target = root / path
            if not target.exists() or target.read_text(encoding='utf-8') != expected:
                errors.append('Stale generated roadmap: ' + path)
            if len(parsed[path].ids) != len(set(parsed[path].ids)):
                errors.append('Duplicate generated HTML anchors: ' + path)
            for reference in parsed[path].references:
                parsed_reference = urlsplit(reference)
                if parsed_reference.scheme or parsed_reference.netloc:
                    continue
                destination = (root / path).parent / unquote(parsed_reference.path) if parsed_reference.path else root / path
                destination = destination.resolve()
                relative = destination.relative_to(root.resolve()).as_posix() if destination.is_relative_to(root.resolve()) else None
                if relative in parsed and parsed_reference.fragment and unquote(parsed_reference.fragment) not in parsed[relative].ids:
                    errors.append(f'{path}: missing roadmap anchor {reference}')
        if any(identifier not in parsed[PAGE].ids for identifier in anchors):
            errors.append('Missing legacy roadmap anchors on dashboard')
        for identifier in ids + phase_ids + milestone_ids + [d['id'] for d in data['sequencing_decisions'] + data['open_decisions']]:
            if identifier not in parsed[anchor_page(data, identifier)].ids:
                errors.append('Missing canonical roadmap anchor: ' + identifier)
            if identifier not in phase_ids and parsed[PAGE].link_targets.get(identifier) != address(anchor_page(data, identifier), PAGE, identifier):
                errors.append('Legacy roadmap shortcut must open its canonical definition: ' + identifier)
        rendered_epics = [identifier for document in parsed.values() for identifier in document.epic_ids]
        if Counter(rendered_epics) != Counter(ids):
            errors.append('Each epic must have one detailed definition on its own canonical page')
        for epic in data['epics']:
            identifier = epic['id']
            page = anchor_page(data, identifier)
            phase = phase_page(epic['phase'])
            if parsed[page].epic_ids != [identifier]:
                errors.append(f'{identifier}: canonical page must contain only its own epic')
            if parsed[phase].link_targets.get(identifier) != address(page, phase, identifier):
                errors.append(f'{identifier}: phase bookmark must link to its canonical epic page')
            for number in range(1, len(epic['acceptance_criteria']) + 1):
                anchor = f'{identifier}-AC-{number}'
                if anchor not in parsed[page].ids:
                    errors.append(f'{identifier}: missing acceptance criterion anchor {anchor}')
        for ticket in tickets:
            identifier = ticket['id']
            page = ticket_page(identifier)
            parent = anchor_page(data, ticket['parent_epic'])
            if identifier not in parsed[page].ids:
                errors.append(f'{identifier}: missing canonical ticket anchor')
            if address(page, parent, identifier) not in parsed[parent].references:
                errors.append(f'{identifier}: missing parent-to-ticket link')
            if address(parent, page, ticket['parent_epic']) not in parsed[page].references:
                errors.append(f'{identifier}: missing ticket-to-parent link')
            for anchor in ticket['epic_criteria']:
                if address(parent, page, anchor) not in parsed[page].references:
                    errors.append(f'{identifier}: missing exact epic AC link {anchor}')
        if any(parsed[phase_page(p)].epic_ids for p in data['phases']):
            errors.append('Phase indexes must link to epic details rather than embed them')
        if parsed[PAGE].epic_ids:
            errors.append('Dashboard must link to epic details rather than embed them')
    return errors


def main():
    data = load()
    errors = roadmap_errors(data)
    summary = progress(data['epics'])
    print(json.dumps({'passed': not errors, 'phases': len(data['phases']), 'epics': summary['total'],
                      'tickets': len(data['tickets']), 'statuses': summary['counts'],
                      'completion_percentage': summary['percentage'], 'errors': errors}, indent=2))
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
