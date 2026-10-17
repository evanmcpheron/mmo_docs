"""Check inventory metadata, evidence, coverage and reproducible static output."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_data_inventory import expected_outputs, load_registry, stale_outputs, totals, validate_registry


def inventory_errors():
    registry = load_registry()
    errors = validate_registry(registry)
    if not errors:
        errors.extend('Stale generated output: ' + path for path in stale_outputs(expected_outputs(registry)))
    return registry, errors


def main():
    registry, errors = inventory_errors()
    print(json.dumps({'passed': not errors, **totals(registry), 'errors': errors}, indent=2))
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
