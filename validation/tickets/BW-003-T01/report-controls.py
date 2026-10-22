import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path.cwd() / 'tools'))
from check_runtime_fixtures import CONTROLS, selected_cases, verified_control, verify_report

parser = argparse.ArgumentParser()
parser.add_argument('--run', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
run = json.loads((args.run / 'run.json').read_text())
native = json.loads((args.run / 'native/fixture-evidence.json').read_text())
arguments = (selected_cases(), run['nonce'], run['source_sha256'],
             hashlib.sha1(Path('fixtures/content_admission/contracts.snapshot.json').read_bytes()).hexdigest(), run['process'])
verify_report(native, *arguments)
mutations = {
    'stale_nonce': lambda value: value.update(nonce='prior-run'),
    'foreign_source': lambda value: value.update(source_sha256='foreign'),
    'missing_assertion': lambda value: value['checks'].pop(),
    'duplicate_assertion': lambda value: value['checks'].append(value['checks'][0]),
    'missing_testcheck': lambda value: value['observations']['assertions'].pop(),
    'unknown_scenario': lambda value: value['observations']['fixtures'][0]['specification'].update(scenario='unknown'),
    'missing_runner': lambda value: value['observations']['fixtures'][0]['run_evidence'].pop('runner_id'),
    'null_runner': lambda value: value['observations']['fixtures'][0]['run_evidence'].update(runner_id=None),
    'null_time': lambda value: value['observations']['fixtures'][0]['run_evidence'].update(completed_at=None),
    'invalid_utc': lambda value: value['observations']['fixtures'][0]['run_evidence'].update(completed_at='2026-02-30T00:00:00Z'),
    'foreign_rules': lambda value: value['observations']['fixtures'][0]['run_evidence'].update(rules_version='foreign'),
    'duplicate_fixture': lambda value: value['observations']['fixtures'].append(value['observations']['fixtures'][0]),
}
results = []
for name, mutate in mutations.items():
    value = copy.deepcopy(native)
    mutate(value)
    try:
        verify_report(value, *arguments)
    except (ValueError, KeyError, TypeError) as error:
        results.append({'case': name, 'rejected': True, 'error': str(error)})
    else:
        raise SystemExit('Unexpected acceptance: ' + name)

def inventory():
    return {str(path.relative_to(args.run)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in args.run.rglob('*') if path.is_file()}

before = inventory()
command = [sys.executable, 'tools/check_runtime_fixtures.py', '--suite', 'evidence', '--output', str(args.run)]
process = subprocess.run(command, capture_output=True, text=True)
reuse = {'command': command, 'exit_status': process.returncode, 'unchanged': before == inventory(),
         'error': process.stderr.strip().splitlines()[-1]}
assert process.returncode != 0 and reuse['unchanged']
unavailable = []
for control in CONTROLS:
    output = args.output / ('unavailable-' + control)
    command = [sys.executable, 'tools/check_runtime_fixtures.py', '--suite', 'evidence', '--control', control,
               '--engine', 'artifacts/deliberately-unavailable-engine', '--output', str(output)]
    process = subprocess.run(command, capture_output=True, text=True)
    report = json.loads((output / 'run.json').read_text())
    assert process.returncode != 0 and not verified_control(output, control)
    assert report['runtime_execution'] == 'Not Executed' and report['stage'] == 'preflight'
    unavailable.append({'control': control, 'command': command, 'exit_status': process.returncode,
                        'control_verified': False, 'stage': report['stage'], 'error': report['error']})
report = {'command': sys.argv, 'source_sha256': run['source_sha256'], 'actual_report_verified': True,
          'native_report': str(args.run / 'native/fixture-evidence.json'),
          'mutations': results, 'reused_output': reuse, 'unavailable_engine': unavailable}
(args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print('Verified actual report, 12 rejected mutations, preserved reused output, and all five unavailable-engine controls.')
