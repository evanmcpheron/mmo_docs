"""Run focused iteration checks or the comprehensive documentation PR gate."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_data_inventory import INVENTORY_PAGE, load_registry
from build_development_roadmap import generated_page_paths, load

ROADMAP_TESTS = {'test_development_roadmap', 'test_data_inventory'}
CONTRACT_TESTS = {'test_data_inventory', 'test_data_model', 'test_reviewed_contracts'}
FULL_CHECKS = ('html-format', 'aggregate', 'python', 'browser-cleanup', 'browser', 'engine-artifacts')


def changed_files(root=ROOT, base='origin/main'):
    def git(*arguments):
        return subprocess.check_output(['git', *arguments], cwd=root, stderr=subprocess.PIPE)

    revision = git('merge-base', 'HEAD', base).decode().strip()
    if not revision:
        raise ValueError('No merge base with ' + base)
    paths = set()
    for arguments in (
        ('diff', '--name-only', '--no-renames', '-z', revision, 'HEAD', '--'),
        ('diff', '--cached', '--name-only', '--no-renames', '-z', '--'),
        ('diff', '--name-only', '--no-renames', '-z', '--'),
        ('ls-files', '--others', '--exclude-standard', '-z'),
    ):
        paths.update(os.fsdecode(path) for path in git(*arguments).split(b'\0') if path)
    return sorted(paths), revision


def select_checks(paths, root=ROOT):
    if not paths:
        return 'full', [], 'No changed files establish a focused task scope'
    try:
        registry = load_registry(root)
        roadmap = {'sources/development-roadmap.json', 'sources/roadmap-audit.html.inc',
                   'sources/roadmap-reuse-review.html.inc',
                   *generated_page_paths(load(root))}
        contracts = {'sources/data-inventory.json', 'sources/data-model.schema.json',
                     INVENTORY_PAGE, 'validation/data-model-review.txt'}
        shared_outputs = {'assets/search-index.js', 'data/manifest.json'}
        data = {binding['path'] for binding in registry['sample_bindings']}
        data.update(source['path'] for source in registry['reviewed_sources'])
    except (OSError, ValueError, KeyError, TypeError) as error:
        return 'full', [], 'Cannot establish generator dependencies: ' + str(error)
    tests = set()
    browser = False
    shared_changed = False
    for path in paths:
        if path in roadmap:
            tests.update(ROADMAP_TESTS)
            browser = True
        elif path in contracts:
            tests.update(CONTRACT_TESTS)
            browser = True
        elif path in shared_outputs:
            shared_changed = True
            browser = True
        elif path in data and path.startswith('data/') and path.endswith('.json'):
            tests.update(CONTRACT_TESTS)
        else:
            return 'full', [], 'Unknown or cross-cutting dependency: ' + path
    if shared_changed:
        tests.update({'test_data_inventory'} if tests else ROADMAP_TESTS | CONTRACT_TESTS)
    checks = ['html-format', 'aggregate', 'python', 'engine-artifacts']
    if browser:
        checks.insert(3, 'browser')
    return 'fast', sorted(tests), checks


def commands(mode, tests, checks, report_dir=None, documentation_only=False):
    durations = ['--durations', '15'] if sys.version_info >= (3, 12) else []
    python_tests = ([sys.executable, '-m', 'unittest', 'discover', '-s', 'validation', '-p', 'test_*.py']
                    if mode == 'full' else [sys.executable, '-m', 'unittest', *tests])
    available = {
        'html-format': ['npm', 'run', 'format:check'],
        'aggregate': [sys.executable, 'validation/run_checks.py', '--read-only'],
        'python': [*python_tests, *durations],
        'browser-cleanup': ['node', '--test', 'validation/test_browser_cleanup.mjs'],
        'browser': ['node', 'validation/check_inventory_browser.mjs', '--read-only'],
        'engine-artifacts': [sys.executable, 'validation/check_engine_artifacts.py'],
    }
    if report_dir is not None:
        available['aggregate'].extend(['--report', str(report_dir / 'report.json')])
        available['browser'].extend(['--report', str(report_dir / 'data-inventory-browser-checks.json')])
    if mode == 'full':
        available['browser'].extend(['--screenshots', str(ROOT / '.git/validation-tmp/screenshots')])
    elif documentation_only:
        available['aggregate'].extend(['--scope', 'documentation'])
    return [(name, available[name]) for name in checks]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('fast', 'full'), default='full')
    parser.add_argument('--base', default='origin/main', help='FAST task base; compare through its merge base with HEAD')
    parser.add_argument('--explain', action='store_true', help='Print the plan without executing checks')
    parser.add_argument('--report-dir', type=Path, help='Explicit directory for fresh reports in existing evidence formats')
    args = parser.parse_args(argv)
    mode, tests, checks = 'full', [], FULL_CHECKS
    paths, revision, reason = [], None, 'Comprehensive verification requested'
    if args.mode == 'fast':
        try:
            paths, revision = changed_files(base=args.base)
            mode, tests, selection = select_checks(paths)
            if mode == 'fast':
                checks, reason = selection, 'Focused source/generator dependencies'
            else:
                reason = selection
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            reason = 'Changed-file detection failed: ' + str(error)
    documentation_only = mode == 'fast' and not any(
        path.startswith('data/') and path != 'data/manifest.json' for path in paths)
    plan = commands(mode, tests, checks, args.report_dir.resolve() if args.report_dir else None,
                    documentation_only=documentation_only)
    deferred = [name for name in FULL_CHECKS if name not in checks]
    if mode == 'fast':
        deferred.append('Python modules outside: ' + ', '.join(tests))
    if documentation_only:
        deferred.append('Allocation cases, capstone routes and allocation-example freshness (unchanged data inputs)')
    print(f'Requested {args.mode.upper()}; executing {mode.upper()}: {reason}', flush=True)
    if args.mode == 'fast':
        print('Changed files: ' + json.dumps(paths) + '; merge base: ' + str(revision), flush=True)
    print('Deferred to FULL: ' + (', '.join(deferred) or 'none'), flush=True)
    for name, command in plan:
        print(name + ': ' + shlex.join(command), flush=True)
    if args.explain:
        return 0
    revisions = {}
    for key, reference in (('revision', 'HEAD'), ('main_revision', 'origin/main')):
        try:
            revisions[key] = subprocess.check_output(['git', 'rev-parse', '--verify', reference],
                                                    cwd=ROOT, text=True, stderr=subprocess.PIPE).strip()
        except (OSError, subprocess.CalledProcessError):
            revisions[key] = None
    temporary = ROOT / '.git/validation-tmp'
    temporary.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, TMPDIR=str(temporary),
                       PYTHONPATH=os.pathsep.join([str(ROOT / 'validation'), os.environ.get('PYTHONPATH', '')]))
    results = []
    start = time.perf_counter()
    for name, command in plan:
        stage_start = time.perf_counter()
        print('\nRUN ' + name, flush=True)
        try:
            result = subprocess.run(command, cwd=ROOT, env=environment)
            code = result.returncode
        except OSError as error:
            print(f'FAIL {name}: {error}', flush=True)
            code = 1
        results.append({'name': name, 'command': command, 'exit_code': code,
                        'seconds': round(time.perf_counter() - stage_start, 3)})
        print(f'{"PASS" if code == 0 else "FAIL"} {name}: {results[-1]["seconds"]}s', flush=True)
    failed = any(result['exit_code'] for result in results)
    summary = {**revisions, 'requested_mode': args.mode, 'executed_mode': mode, 'reason': reason,
               'merge_base': revision, 'changed_files': paths, 'checks': results, 'deferred': deferred,
               'passed': not failed, 'seconds': round(time.perf_counter() - start, 3)}
    if args.report_dir:
        args.report_dir.mkdir(parents=True, exist_ok=True)
        (args.report_dir / 'validation-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(f'\n{mode.upper()} {"FAIL" if failed else "PASS"}: {summary["seconds"]}s; '
          + ('focused checks only; FULL still required' if mode == 'fast' else 'comprehensive gate'), flush=True)
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
