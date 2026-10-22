import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description='Replay report integrity controls using actual native output.')
parser.add_argument('--game-root', type=Path, required=True)
parser.add_argument('--run', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
sys.path.insert(0, str(args.game_root.resolve() / 'tools'))
from check_content_admission import (
    SUITE_TESTS, expected_checks, expected_admission_checks, expected_binding_checks,
    expected_economy_checks, verify_automation, verify_native,
)

read = lambda path: json.loads(path.read_text(encoding='utf-8-sig'))
run = read(args.run / 'run.json')
assert run['status'] == 'Passed' and run['runtime_execution'] == 'Executed'
builders = {'compatibility': expected_checks, 'admission': expected_admission_checks,
            'bindings': expected_binding_checks, 'economy': expected_economy_checks}
required = {}
for name, builder in builders.items():
    required.update(builder(read(args.game_root / 'fixtures/content_admission' / (name + '.json'))))
snapshot_sha1 = hashlib.sha1((args.game_root / 'fixtures/content_admission/contracts.snapshot.json').read_bytes()).hexdigest()
controls = []
for name, identities in required.items():
    path = args.run / 'native' / (name + '.json')
    actual = read(path)
    arguments = (name, run['nonce'], run['source_sha256'], snapshot_sha1, identities)
    assert verify_native(actual, *arguments) == len(identities)
    for mutation in ('partial', 'duplicate', 'foreign-nonce', 'foreign-source', 'failed-assertion'):
        modified = copy.deepcopy(actual)
        if mutation == 'partial':
            modified['checks'].pop()
        elif mutation == 'duplicate':
            modified['checks'].append(copy.deepcopy(modified['checks'][0]))
        elif mutation == 'foreign-nonce':
            modified['nonce'] = 'foreign-execution'
        elif mutation == 'foreign-source':
            modified['source_sha256'] = '0' * 64
        else:
            modified['checks'][0]['passed'] = False
        try:
            verify_native(modified, *arguments)
        except ValueError as error:
            controls.append({'suite': name, 'mutation': mutation, 'rejected': True, 'error': str(error),
                             'original_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        else:
            raise AssertionError(f'Accepted {name}/{mutation}')
automation = read(args.run / 'automation/index.json')
verify_automation(automation, SUITE_TESTS['all'])
for mutation in ('partial', 'duplicate', 'foreign', 'failed'):
    modified = copy.deepcopy(automation)
    if mutation == 'partial':
        modified['tests'].pop()
    elif mutation == 'duplicate':
        modified['tests'].append(copy.deepcopy(modified['tests'][0]))
    elif mutation == 'foreign':
        modified['tests'][0]['fullTestPath'] = 'Foreign.Test'
    else:
        modified['tests'][0]['state'] = 'Fail'
    try:
        verify_automation(modified, SUITE_TESTS['all'])
    except ValueError as error:
        controls.append({'suite': 'automation', 'mutation': mutation, 'rejected': True, 'error': str(error)})
    else:
        raise AssertionError(f'Accepted automation/{mutation}')
report = {'result': 'Passed', 'source_sha256': run['source_sha256'], 'nonce': run['nonce'],
          'positive_native_counts': {name: len(ids) for name, ids in required.items()},
          'positive_automation_tests': sorted(SUITE_TESTS['all']), 'controls': controls,
          'scope': 'Actual native reports replayed through the production report verifiers; no economic rule is calculated in Python.'}
with args.output.open('x') as stream:
    json.dump(report, stream, indent=2)
    stream.write('\n')
print(f'{len(controls)} actual-report controls rejected; complete originals passed')
