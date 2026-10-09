#!/usr/bin/env python3
"""Validate phase accounting and required editorial section structure."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def check() -> dict:
    phases = json.loads((ROOT / 'sources/phase-integration.json').read_text(encoding='utf-8'))['phases']
    assets = json.loads((ROOT / 'sources/current-asset-manifest.json').read_text(encoding='utf-8'))['assets']
    pages = {record['path']: record for record in json.loads((ROOT / 'sources/manual-pages.json').read_text(encoding='utf-8'))['pages']}
    errors = []
    if [record['phase'] for record in phases] != list(range(32)):
        errors.append('Expected phases 00–31 exactly once in order')
    for phase in phases:
        number = phase['phase']
        page = pages.get(f'phases/phase-{number:02d}.html')
        if not page or len(page['sections']) != 10:
            errors.append(f'Phase {number}: expected ten authored sections')
        for field in ['editor_steps', 'native_contract', 'reopen_consumers', 'run_now', 'rejection', 'regression']:
            if not phase.get(field):
                errors.append(f'Phase {number}: missing {field}')
        if set(phase['creates']) != {asset['name'] for asset in assets if asset['first_phase'] == number}:
            errors.append(f'Phase {number}: incorrect creation set')
        if set(phase['activates']) != {asset['name'] for asset in assets if asset['first_active_phase'] == number}:
            errors.append(f'Phase {number}: incorrect activation set')
        if phase['dependencies'] != ([number - 1] if number else []):
            errors.append(f'Phase {number}: sequential prerequisite mismatch')
        if phase['runtime_test'] != 'not_run':
            errors.append(f'Phase {number}: unsupported runtime status')
    return {'status': 'pass' if not errors else 'fail', 'phases': len(phases), 'scope': 'Structure and present-registry integration accounting, not exhaustive Editor instructions or runtime integration', 'errors': errors}
if __name__ == '__main__':
    result = check()
    (ROOT / 'verification/phase-integration.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result['errors']))
