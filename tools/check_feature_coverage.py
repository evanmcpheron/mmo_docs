#!/usr/bin/env python3
"""Check source-block traceability; strict mode rejects incomplete coverage."""
import argparse
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def check(require_complete: bool=False) -> dict:
    source = json.loads((ROOT / 'sources/feature-coverage.json').read_text(encoding='utf-8'))
    lines = (ROOT / source['source']).read_text(encoding='utf-8').splitlines()
    errors = []
    identities = set()
    for record in source['requirements']:
        if record['id'] in identities:
            errors.append('Duplicate requirement ID ' + record['id'])
        identities.add(record['id'])
        excerpt = '\n'.join(lines[record['source_line_start'] - 1:record['source_line_end']])
        if excerpt != record['source_text']:
            errors.append('Source text/range mismatch ' + record['id'])
        if not (ROOT / record['chapter']).is_file():
            errors.append('Missing chapter ' + record['id'])
        for key in ['owner', 'solo_test', 'two_client_test']:
            if not record.get(key):
                errors.append(f"{record['id']}: missing {key}")
        if not 0 <= record['phase'] <= 31:
            errors.append('Invalid phase ' + record['id'])
    incomplete = [requirement['id'] for requirement in source['requirements'] if not requirement['complete']]
    if require_complete and (not source['complete'] or incomplete):
        errors.append(f'Full master-prompt coverage is incomplete: {len(incomplete)} initial-contract source blocks plus blocked source audits and editorial gaps.')
    return {'status': 'pass' if not errors else 'fail', 'mode': 'strict-completion' if require_complete else 'source-block-accounting', 'requirement_blocks': len(identities), 'incomplete_blocks': len(incomplete), 'full_guide_complete': False, 'scope': 'Grouped requirements preserve source text; accounting does not certify atomic-feature completeness', 'errors': errors}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    report = check(args.require_complete)
    name = 'coverage-strict.json' if args.require_complete else 'coverage-accounting.json'
    (ROOT / 'verification' / name).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    raise SystemExit(bool(report['errors']))
