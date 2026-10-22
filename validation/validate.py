"""Focused documentation verification. QUICK is local default; --gate checks PR freshness."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_data_inventory import load_registry
from build_development_roadmap import generated_page_paths, load

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


def affected_tests(paths, root=ROOT):
    modules = {path.stem: path for directory in ('validation', 'scripts') for path in (root / directory).glob('*.py')}
    affected = {Path(path).stem for path in paths if path.endswith('.py')}
    if any(Path(path).name in {'format_html.mjs', '.prettierrc.json', 'package.json', 'package-lock.json'} for path in paths):
        affected.add('html_format')
    imports = {}
    for name, path in modules.items():
        tree = ast.parse(path.read_text(), filename=str(path))
        imports[name] = {node.module.split('.')[0] for node in ast.walk(tree)
                         if isinstance(node, ast.ImportFrom) and node.module}
        imports[name].update(alias.name.split('.')[0] for node in ast.walk(tree)
                             if isinstance(node, ast.Import) for alias in node.names)
    while True:
        expanded = affected | {name for name, dependencies in imports.items() if dependencies & affected}
        if expanded == affected:
            return sorted(name for name in affected if name.startswith('test_') and name in modules)
        affected = expanded


def select_checks(paths, root=ROOT):
    checks = set()
    unresolved = []
    try:
        registry = load_registry(root)
        roadmap = {'sources/development-roadmap.json', 'sources/roadmap-audit.html.inc',
                   'sources/roadmap-reuse-review.html.inc', *generated_page_paths(load(root))}
        data = {binding['path'] for binding in registry['sample_bindings']}
        data.update(source['path'] for source in registry['reviewed_sources'])
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {'checks': [], 'tests': [], 'unresolved': ['Cannot establish dependencies: ' + str(error)]}
    for path in paths:
        file = Path(path)
        if path in roadmap:
            checks.update(('roadmap', 'freshness', 'site'))
        elif path in {'sources/data-inventory.json', 'sources/data-model.schema.json', 'guide/data-inventory.html'} or (path in data and path.startswith('data/')):
            checks.update(('contracts', 'freshness'))
            if path.startswith('data/') and path != 'data/manifest.json':
                checks.add('data')
            if path.endswith(('character_catalog.json', 'talents.json', 'allocation_examples.json', 'classes.json', 'specializations.json')):
                checks.add('allocations')
        elif path in {'data/manifest.json', 'assets/search-index.js'}:
            checks.update(('roadmap', 'freshness', 'site'))
        elif path.endswith('.html'):
            checks.update(('contracts', 'freshness', 'site'))
        elif path.startswith(('scripts/', 'validation/')) and file.suffix in {'.py', '.mjs'}:
            if not (root / path).exists():
                unresolved.append('Deleted tooling needs consumer review: ' + path)
            if (file.suffix == '.mjs' and not file.name.startswith('test_')) or file.name in {
                    'html_format.py', 'build_development_roadmap.py', 'build_data_inventory.py'}:
                checks.add('browser')
            if 'roadmap' in path:
                checks.update(('roadmap', 'freshness', 'site'))
            elif 'data' in path or 'model' in path:
                checks.update(('contracts', 'freshness'))
            elif file.name == 'run_checks.py':
                checks.update(('data', 'allocations', 'site', 'contracts', 'roadmap', 'freshness'))
        elif path.startswith('assets/') or file.name in {'package.json', 'package-lock.json', '.prettierrc.json', '.prettierignore'}:
            checks.update(('site', 'freshness', 'browser'))
        elif path.startswith(('docs/', '.agents/', '.github/', 'validation/')) or file.suffix in {'.md', '.txt'} or file.name == '.gitignore':
            continue
        else:
            unresolved.append('Unclassified input; resolve its verification before PR delivery: ' + path)
    return {'checks': sorted(checks), 'tests': affected_tests(paths, root), 'unresolved': unresolved}


def commands(mode, impact, paths, gate=False, report_dir=None):
    python = sys.executable
    available = {
        'html-format': ['npm', 'run', 'format:check'],
        'aggregate': [python, 'validation/run_checks.py', '--read-only'],
        'python': [python, '-m', 'unittest', 'discover', '-s', 'validation', '-p', 'test_*.py'],
        'browser-cleanup': ['node', '--test', 'validation/test_browser_cleanup.mjs'],
        'browser': ['node', 'validation/check_inventory_browser.mjs', '--read-only'],
        'engine-artifacts': [python, 'validation/check_engine_artifacts.py'],
    }
    if report_dir:
        available['aggregate'].extend(['--report', str(report_dir / 'report.json')])
        available['browser'].extend(['--report', str(report_dir / 'browser.json')])
    if mode == 'full':
        return [(name, available[name]) for name in FULL_CHECKS]
    checks = set(impact['checks'])
    plan = [('whitespace', ['git', 'diff', '--check']), ('staged-whitespace', ['git', 'diff', '--cached', '--check'])]
    source_checks = checks & {'roadmap', 'contracts', 'site'}
    if not gate and not any(path.endswith('.html') or path == 'assets/search-index.js' for path in paths):
        source_checks.discard('site')
    structural = [path for path in paths if Path(path).suffix in {'.json', '.py'} and (ROOT / path).is_file()]
    if source_checks or structural or (gate and 'freshness' in checks):
        command = [python, 'validation/check_sources.py']
        for scope in sorted(source_checks):
            command.extend(['--scope', scope])
        if gate and 'freshness' in checks:
            command.extend(['--scope', 'freshness'])
        command.extend(['--paths', *structural])
        plan.append(('sources', command))
    if impact['tests']:
        plan.append(('python', [python, '-m', 'unittest', *impact['tests']]))
    if gate and 'data' in checks:
        plan.append(('data', [python, 'validation/run_checks.py', '--read-only', '--scope',
                              'data' if 'allocations' in checks else 'data-structure']))
    if any(Path(path).name in {'browser_cleanup.mjs', 'test_browser_cleanup.mjs'} for path in paths):
        plan.append(('browser-cleanup', available['browser-cleanup']))
    if mode == 'integration' and 'browser' in checks:
        plan.extend((name, available[name]) for name in ('browser-cleanup', 'browser')
                    if name not in {item[0] for item in plan})
    if any(path.endswith('.mjs') for path in paths):
        for path in paths:
            if path.endswith('.mjs') and (ROOT / path).is_file():
                plan.append(('syntax-' + Path(path).stem, ['node', '--check', path]))
    if any(path.endswith(('.gd', '.tscn', '.godot')) for path in paths):
        plan.append(('engine-artifacts', available['engine-artifacts']))
    return plan


def git_reference(reference):
    try:
        value = subprocess.check_output(['git', 'rev-parse', '--verify', reference], cwd=ROOT, text=True, stderr=subprocess.PIPE)
        return value.strip() if isinstance(value, str) else None
    except (OSError, subprocess.SubprocessError):
        return None


def input_identity(root=ROOT, changed=()):
    try:
        paths = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root).split(b'\0')
    except (OSError, subprocess.SubprocessError):
        return None
    names = {os.fsdecode(name) for name in paths if name}
    names = {name for name in names if not name.startswith(('validation/tickets/', 'validation/epics/', 'validation/performance/'))} | set(changed)
    identities = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                  for name in sorted(names) if (root / name).is_file()}
    return hashlib.sha256(json.dumps(identities, sort_keys=True).encode()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('quick', 'native', 'integration', 'full', 'fast'), default='quick')
    parser.add_argument('--base', default='origin/main')
    parser.add_argument('--gate', action='store_true', help='Check generated freshness and block unsupported PR verification')
    parser.add_argument('--explain', action='store_true')
    parser.add_argument('--report-dir', type=Path)
    args = parser.parse_args(argv)
    mode = 'quick' if args.mode == 'fast' else args.mode
    if mode == 'native':
        print('NOT RUN: documentation has no Unreal environment; use GAME_ROOT/tools/validate.py --mode native')
        return 2
    paths, revision = [], None
    detection_error = None
    try:
        paths, revision = changed_files(base=args.base)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        detection_error = 'Cannot establish Git scope: ' + str(error)
    try:
        impact = select_checks(paths)
    except (SyntaxError, OSError, ValueError) as error:
        impact = {'checks': [], 'tests': [], 'unresolved': ['Cannot analyze tooling: ' + str(error)]}
    outstanding = list(impact['unresolved'])
    if detection_error:
        outstanding.append(detection_error)
    if mode != 'full':
        if 'browser' in impact['checks'] and mode != 'integration':
            outstanding.append('INTEGRATION required for changed browser/template/UI behavior')
        if 'freshness' in impact['checks'] and not args.gate:
            outstanding.append('PR freshness required: rerun with --gate after generation')
        if 'data' in impact['checks'] and not args.gate:
            outstanding.append('PR data invariants required: --gate (allocations only for affected inputs)')
    plan = commands(mode, impact, paths, args.gate, args.report_dir)
    if revision:
        plan.insert(0, ('branch-whitespace', ['git', 'diff', '--check', revision, 'HEAD']))
    print(f'Requested {args.mode.upper()}; executing {mode.upper()}', flush=True)
    print('Impact: ' + json.dumps(impact), flush=True)
    print('Outstanding: ' + json.dumps(outstanding), flush=True)
    for name, command in plan:
        print(name + ': ' + shlex.join(command), flush=True)
    if args.explain:
        return 2 if args.gate and outstanding else 0
    temporary = ROOT / '.git/validation-tmp'
    temporary.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, TMPDIR=str(temporary), PYTHONPATH=str(ROOT / 'validation'))
    results = []
    start = time.perf_counter()
    initial_identity = input_identity(changed=paths)
    for name, command in plan:
        stage_start = time.perf_counter()
        try:
            code = subprocess.run(command, cwd=ROOT, env=environment).returncode
        except OSError as error:
            print(f'NOT RUN {name}: {error}', flush=True)
            code = 1
        results.append({'name': name, 'command': command, 'exit_code': code,
                        'seconds': round(time.perf_counter() - stage_start, 3)})
        print(f'{"PASS" if code == 0 else "FAIL"} {name}: {results[-1]["seconds"]}s', flush=True)
        if code:
            outstanding.append('Not run after failure: ' + ', '.join(item[0] for item in plan[len(results):]))
            break
    final_identity = input_identity(changed=paths)
    passed = initial_identity is not None and initial_identity == final_identity and all(result['exit_code'] == 0 for result in results)
    summary = {'revision': git_reference('HEAD'), 'main_revision': git_reference(args.base),
               'requested_mode': args.mode, 'executed_mode': mode, 'merge_base': revision,
               'changed_files': paths, 'checks': results, 'outstanding': outstanding,
               'source_sha256': final_identity, 'source_stable': initial_identity == final_identity,
               'environment': {'platform': sys.platform + '-' + platform.machine(), 'python': platform.python_version()},
               'passed': passed, 'complete': passed and not outstanding,
               'seconds': round(time.perf_counter() - start, 3)}
    if args.report_dir:
        args.report_dir.mkdir(parents=True, exist_ok=True)
        (args.report_dir / 'validation-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(f'{mode.upper()} {"PASS" if passed else "FAIL"}: {summary["seconds"]}s; '
          f'selected documentation checks only; complete={summary["complete"]}', flush=True)
    return 1 if not passed else (2 if args.gate and outstanding else 0)


if __name__ == '__main__':
    raise SystemExit(main())
