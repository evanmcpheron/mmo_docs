"""Validate the independent Unreal C++ reference and optional zero-progress snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_data_inventory import reviewed_content
from build_development_roadmap import milestone_progress, progress


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


def contract_content(inventory):
    return {key: value for key, value in inventory.items() if key not in ('pages', 'audit_notes')}


def foundation_errors(root=ROOT, roadmap=None):
    errors = []
    if roadmap is None:
        roadmap = json.loads((root / 'sources/development-roadmap.json').read_text())
    epics = {epic['id']: epic for epic in roadmap['epics']}
    plugin = epics.get('BW-100')
    if plugin is None or 'BW-001' not in plugin['hard_dependencies']:
        errors.append('Supplied plugin verification must require the native build baseline')
    for identifier in ('BW-004', 'BW-005'):
        if identifier not in epics or 'BW-100' not in epics[identifier]['hard_dependencies']:
            errors.append(f'{identifier}: dependent networking must require supplied plugin verification')
    if (root / '.gitmodules').exists():
        errors.append('Documentation must not require implementation submodules')
    for path in root.rglob('*'):
        if any(part in ('.git', 'node_modules', '__pycache__') for part in path.relative_to(root).parts):
            continue
        if path.suffix in ('.uproject', '.uplugin', '.uasset', '.umap'):
            errors.append(f'Game project or implementation asset inside documentation: {path.relative_to(root)}')
    foundation = (root / 'guide/unreal-cpp.html').read_text()
    for phrase in ('Unreal Engine 5', 'C++', 'dedicated servers', 'server-authoritative'):
        if phrase not in foundation:
            errors.append(f'Foundation missing project requirement: {phrase}')
    return errors


def baseline_errors(root=ROOT, roadmap=None, inventory=None):
    if roadmap is None:
        roadmap = json.loads((root / 'sources/development-roadmap.json').read_text())
    if inventory is None:
        inventory = json.loads((root / 'sources/data-inventory.json').read_text())
    snapshot = json.loads((root / 'validation/foundation-baseline.json').read_text())
    errors = []
    for kind in ('epics', 'tickets'):
        for record in roadmap[kind]:
            if record['status'] != 'Not Started' or record['verified_evidence'] or record['blockers']:
                errors.append(f'{record["id"]}: zero baseline requires Not Started and empty evidence/blockers')
    for milestone in roadmap['milestones']:
        if milestone_progress(roadmap, milestone)['status'] != 'Not Started':
            errors.append(f'{milestone["id"]}: milestone is not at the zero baseline')
    for phase in roadmap['phases']:
        if progress([e for e in roadmap['epics'] if e['phase'] == phase['id']])['status'] != 'Not Started':
            errors.append(f'{phase["id"]}: phase is not at the zero baseline')
    for directory in ('validation/tickets', 'validation/epics'):
        path = root / directory
        if path.exists() and any(path.rglob('*')):
            errors.append(f'Runtime evidence retained in zero baseline: {directory}')
    if digest(contract_content(inventory)) != snapshot['canonical_contracts_sha256']:
        errors.append('Canonical contract or relationship changed from the reviewed baseline')
    for name, expected in snapshot['gameplay_files_sha256'].items():
        path = root / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(f'Preserved gameplay catalog changed: {name}')
    for name, expected in snapshot['gameplay_chapters_sha256'].items():
        path = root / name
        if not path.is_file() or hashlib.sha256(reviewed_content(path.read_text()).encode()).hexdigest() != expected:
            errors.append(f'Preserved gameplay chapter changed: {name}')
    if set(snapshot['retained_epic_ids']) - {e['id'] for e in roadmap['epics']}:
        errors.append('An established epic responsibility disappeared')
    if set(snapshot['retained_ticket_ids']) - {t['id'] for t in roadmap['tickets']}:
        errors.append('An equivalent retained ticket responsibility disappeared')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', action='store_true', help='Also verify the preserved zero-progress snapshot')
    args = parser.parse_args()
    errors = foundation_errors()
    if args.baseline:
        errors.extend(baseline_errors())
    if errors:
        raise SystemExit('\n'.join(errors))
    print('Independent Unreal C++ foundation checks passed' + ('; zero baseline and gameplay preservation verified.'
                                                            if args.baseline else '.'))


if __name__ == '__main__':
    main()
