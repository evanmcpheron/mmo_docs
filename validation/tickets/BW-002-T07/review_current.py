import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys


parser = argparse.ArgumentParser(description='Check applicability of retained T07 native evidence.')
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
docs = Path(__file__).resolve().parents[3]
game = docs.parent
prior = docs / 'validation/tickets/BW-002-T06'
sys.path.insert(0, str(game / 'tools'))
from check_baseline import current_binary_identity, source_identity, verified_build_tool, verify_toolchain
from extract_content_contracts import DEFAULT_REGISTRY, DEFAULT_SNAPSHOT, verify_snapshot
from validate import expected_rejection


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def git(root, *arguments):
    return subprocess.check_output(['git', *arguments], cwd=root, text=True).strip()


def require(condition, message):
    if not condition:
        raise ValueError(message)


manifest = read(prior / 'artifact-manifest.json')
for entry in manifest['files']:
    contents = (docs / entry['artifact']).read_bytes()
    require(len(contents) == entry['bytes'] and hashlib.sha256(contents).hexdigest() == entry['sha256'],
            'Retained artifact changed: ' + entry['artifact'])

digest, files = source_identity()
snapshot = verify_snapshot(DEFAULT_REGISTRY, DEFAULT_SNAPSHOT)
review = read(prior / 'review.json')
require(digest == review['source_sha256'], 'Native inputs changed; rerun native FULL')
boundary = hashlib.sha256((game / 'docs/authority-and-lifecycles.md').read_bytes()).hexdigest()
require(boundary == review['ownership_review']['boundary_map_sha256'], 'Boundary review changed')

full = read(prior / 'full/validation-summary.json')
require(full['passed'] and full['initial_source_sha256'] == full['source_sha256'] == digest,
        'Retained FULL is unsuccessful or has different inputs')
controls = []
for check in full['checks']:
    require(check['status'] == 'passed', 'Unsuccessful FULL stage: ' + check['name'])
    if check['expected_rejection']:
        require(expected_rejection(check['name'], prior / 'full' / check['name'], check['exit_code']),
                'Retained control no longer rejects: ' + check['name'])
        controls.append(check['name'])

runs = [read(prior / 'full' / name / 'run.json') for name in ('automation', 'recovery-tests')]
require(runs[0]['nonce'] != runs[1]['nonce'], 'Recovery must be independent')
for run in runs:
    require(run['status'] == 'Passed' and run['runtime_execution'] == 'Executed', 'Native run did not pass')
    require(run['source_sha256'] == digest and run['source_files'] == files, 'Native run input mismatch')
    require(run['snapshot_sha256'] == hashlib.sha256(DEFAULT_SNAPSHOT.read_bytes()).hexdigest(),
            'Canonical snapshot mismatch')
    for suite, expected in run['corpora_sha256'].items():
        corpus = game / 'fixtures/content_admission' / (suite + '.json')
        require(hashlib.sha256(corpus.read_bytes()).hexdigest() == expected, 'Corpus changed: ' + suite)

modules = read(game / 'Binaries/Mac/UnrealEditor.modules')
module = game / 'Binaries/Mac' / modules['Modules']['Briarwake']
require(current_binary_identity(module, digest) == runs[1]['module_sha256'], 'Recovery module changed')

environments = {}
for name in ('editor-build', 'game-build', 'server-build'):
    run = read(prior / 'full' / name / 'run.json')
    require(run['status'] == 'Passed' and run['source_sha256'] == digest, 'Build input mismatch')
    environment = verify_toolchain(Path(run['environment']['engine_root']))
    require(environment == run['environment'], 'Toolchain changed: ' + name)
    environments[name] = environment
_, build_tool = verified_build_tool(Path(environments['game-build']['engine_root']))
require(build_tool == read(prior / 'full/game-build/run.json')['build_tool'], 'Patched build tool changed')

roadmap = read(docs / 'sources/development-roadmap.json')
parent = next(epic for epic in roadmap['epics'] if epic['id'] == 'BW-002')
tickets = {ticket['id']: ticket for ticket in roadmap['tickets'] if ticket['parent_epic'] == 'BW-002'}
require(parent['status'] == 'Complete' and not parent['blockers'], 'Parent gates are unfinished')
require(all(ticket['status'] == 'Complete' and not ticket['blockers'] for ticket in tickets.values()),
        'A child ticket remains unfinished')
parent_review = read(prior / 'parent-review.json')
require([criterion['criterion'] for criterion in parent_review['criteria']] == [1, 2, 3, 4, 5]
        and all(criterion['result'] == 'Passed' for criterion in parent_review['criteria']),
        'Missing five-criterion parent review')

report = {
    'result': 'Passed', 'ticket': 'BW-002-T07',
    'reviewed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'game_main': git(game, 'rev-parse', 'origin/main'),
    'game_revision': git(game, 'rev-parse', 'HEAD'),
    'docs_base_main': git(docs, 'rev-parse', 'origin/main'),
    'native_tested_revision': full['revision'], 'source_sha256': digest,
    'native_input_files': len(files), 'retained_artifacts_verified': len(manifest['files']),
    'changes_since_native_run': git(game, 'diff', '--stat', full['revision'], 'HEAD'),
    'canonical_semantic_sha256': snapshot['semantic_sha256'],
    'canonical_definitions': len(snapshot['$defs']), 'boundary_map_sha256': boundary,
    'native_runs': [{'artifact': 'validation/tickets/BW-002-T06/full/' + name + '/run.json',
                     'nonce': run['nonce'], 'counts': run['assertion_counts'],
                     'module_sha256': run['module_sha256'],
                     'executed_tests': run['executed_tests']}
                    for name, run in zip(('automation', 'recovery-tests'), runs)],
    'retained_full_stages': len(full['checks']), 'revalidated_rejection_controls': controls,
    'toolchains': environments, 'parent_criteria': parent_review['criteria'],
    'parent_criteria_artifact_base': 'validation/tickets/BW-002-T06/',
    'package_isolation': 'validation/tickets/BW-002-T06/package-isolation.json',
    'not_run': full['not_run'],
    'scope': 'Evidence applicability audit; no new native execution. Reuse FULL because all native inputs, '
             'corpora, canonical definitions, Editor module, boundary map and pinned toolchains match. '
             'Replay both report sets separately through check_report_controls.py. No gameplay authority is added.'
}
with args.output.open('x') as stream:
    json.dump(report, stream, indent=2)
    stream.write('\n')
print(f"Passed: {len(files)} native inputs, {len(manifest['files'])} retained artifacts, "
      f"{len(full['checks'])} FULL stages and {len(controls)} rejection controls remain applicable")
