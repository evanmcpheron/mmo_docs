"""Current content checks, separate from tests of the validators and from browser behavior."""
import argparse
import ast
import json
from pathlib import Path

from check_data_inventory import inventory_errors
from check_development_roadmap import roadmap_errors
from run_checks import site_checks
from build_data_inventory import load_registry, validate_registry
from build_development_roadmap import load

ROOT = Path(__file__).resolve().parents[1]


def check_sources(scopes, paths=(), root=ROOT):
    errors = []
    for name in paths:
        path = root / name
        if not path.is_file():
            continue
        try:
            if path.suffix == '.py':
                ast.parse(path.read_text(), filename=name)
            elif path.suffix == '.json':
                json.loads(path.read_text())
        except (OSError, ValueError, SyntaxError) as error:
            errors.append(f'{name}: {error}')
    if errors:
        return errors
    try:
        if 'roadmap' in scopes or 'roadmap-freshness' in scopes:
            errors.extend(roadmap_errors(load(root), root=root, check_generated='roadmap-freshness' in scopes))
        if 'roadmap-freshness' in scopes and not errors:
            from build_development_roadmap import roadmap_outputs
            from build_data_inventory import stale_outputs
            errors.extend('Stale generated roadmap output: ' + path
                          for path in stale_outputs(roadmap_outputs(load(root), root), root))
        if 'contracts-freshness' in scopes:
            errors.extend(inventory_errors()[1])
        elif 'contracts' in scopes:
            errors.extend(validate_registry(load_registry(root), root=root))
        if 'site' in scopes:
            errors.extend(item['name'] + ': ' + item['detail'] for item in site_checks() if not item['passed'])
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        errors.append('Content verification failed: ' + str(error))
    return errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scope', action='append', choices=('roadmap', 'contracts', 'roadmap-freshness', 'contracts-freshness', 'site'), default=[])
    parser.add_argument('--paths', nargs='*', default=[])
    args = parser.parse_args()
    errors = check_sources(args.scope, args.paths)
    print('\n'.join(errors) if errors else 'Selected current content checks passed; no gameplay execution.')
    raise SystemExit(bool(errors))
