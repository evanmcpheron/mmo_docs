"""Validate the registry's JSON Schema vocabulary and its shipped source records.

This deliberately supports only the schema keywords used by this repository.
Unknown keywords fail closed. Semantic x-invariants remain implementation gates.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from datetime import datetime
from decimal import Decimal
from pathlib import Path

SCHEMA_PATH = 'sources/data-model.schema.json'
REPORT_PATH = 'validation/data-model-review.txt'
DIALECT = 'https://json-schema.org/draft/2020-12/schema'
KEYWORDS = {'$ref', 'type', 'description', 'properties', 'required', 'additionalProperties',
            'propertyNames', 'items', 'enum', 'const', 'anyOf', 'oneOf', 'allOf',
            'minimum', 'maximum', 'multipleOf', 'minLength', 'maxLength',
            'minItems', 'maxItems', 'uniqueItems', 'format'}
TYPES = {'object', 'array', 'string', 'integer', 'number', 'boolean', 'null'}


def definitions(registry):
    return {**registry['shared_definitions'], **{e['name']: e['definition'] for e in registry['entries']}}


def schema_bundle(registry):
    entries = {e['name']: e for e in registry['entries']}
    return {
        '$schema': registry['schema_dialect'],
        '$id': 'urn:briarwake:data-model',
        'description': 'Generated from data-inventory.json. Select a named $defs contract. '
                       'Needs Decision contracts validate only the documented portion; '
                       'x-members are symbolic identifiers with no assigned wire encoding.',
        '$defs': {name: dict(schema, **({'x-category': entries[name]['category'],
                  'x-definition-status': entries[name]['definition_status']} if name in entries else {}))
                  for name, schema in sorted(definitions(registry).items())},
    }


def schema_children(schema):
    yield from schema.get('properties', {}).values()
    for key in ('items', 'additionalProperties', 'propertyNames'):
        if isinstance(schema.get(key), dict):
            yield schema[key]
    for key in ('anyOf', 'oneOf', 'allOf'):
        yield from schema.get(key, [])


def type_references(schema, include_identities=True):
    found = set()
    if '$ref' in schema:
        found.add(schema['$ref'].removeprefix('#/$defs/'))
    if include_identities and 'x-reference' in schema:
        found.add(schema['x-reference']['target'])
        found.update(schema['x-reference'].get('alternatives', []))
    for child in schema_children(schema):
        found.update(type_references(child, include_identities))
    return found


def schema_errors(schema, defs, path):
    errors = []
    if not isinstance(schema, dict):
        return [f'{path}: schema must be an object']
    unknown = {k for k in schema if k not in KEYWORDS and not k.startswith('x-')}
    if unknown:
        errors.append(f'{path}: unsupported schema keywords {sorted(unknown)}')
    if not any(k in schema for k in ('type', '$ref', 'const', 'enum', 'anyOf', 'oneOf', 'allOf')):
        errors.append(f'{path}: missing structural type')
    if '$ref' in schema and (not schema['$ref'].startswith('#/$defs/') or
                            schema['$ref'][8:] not in defs):
        errors.append(f'{path}: undefined type reference {schema["$ref"]}')
    if 'type' in schema:
        kinds = schema['type'] if isinstance(schema['type'], list) else [schema['type']]
        if not kinds or not set(kinds) <= TYPES:
            errors.append(f'{path}: invalid schema type')
    if schema.get('type') == 'object':
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        if len(required) != len(set(required)) or not set(required) <= set(properties):
            errors.append(f'{path}: required fields disagree with properties')
        if not properties and not isinstance(schema.get('additionalProperties'), dict):
            errors.append(f'{path}: unstructured object is forbidden')
        if 'additionalProperties' not in schema:
            errors.append(f'{path}: object must explicitly declare additional properties')
        for name, field in properties.items():
            if not field.get('description'):
                errors.append(f'{path}.{name}: missing property semantics')
    if schema.get('type') == 'array' and 'items' not in schema:
        errors.append(f'{path}: array must have typed items')
    for keyword in ('enum', 'x-members'):
        if keyword in schema:
            values = schema[keyword]
            if not isinstance(values, list) or len(values) != len({json.dumps(v, sort_keys=True) for v in values}):
                errors.append(f'{path}: invalid or duplicate {keyword} members')
            if keyword == 'enum' and not values:
                errors.append(f'{path}: serialized enum cannot be empty')
    for keyword in ('oneOf', 'anyOf', 'allOf'):
        if keyword in schema and (not isinstance(schema[keyword], list) or not schema[keyword]):
            errors.append(f'{path}: invalid {keyword}')
    for keyword in ('minimum', 'maximum', 'multipleOf'):
        if keyword in schema and (type(schema[keyword]) not in (int, float) or
                                  not math.isfinite(schema[keyword])):
            errors.append(f'{path}: invalid {keyword}')
    if schema.get('multipleOf', 1) <= 0:
        errors.append(f'{path}: multipleOf must be positive')
    if 'minimum' in schema and 'maximum' in schema and schema['minimum'] > schema['maximum']:
        errors.append(f'{path}: inverted bounds')
    for keyword in ('minLength', 'maxLength', 'minItems', 'maxItems'):
        if keyword in schema and (type(schema[keyword]) is not int or schema[keyword] < 0):
            errors.append(f'{path}: invalid {keyword}')
    if 'format' in schema and schema['format'] != 'date-time':
        errors.append(f'{path}: unsupported format')
    if 'x-reference' in schema:
        targets = [schema['x-reference']['target'], *schema['x-reference'].get('alternatives', [])]
        if any(target not in defs for target in targets):
            errors.append(f'{path}: undefined identity target {targets}')
    if 'x-canonical-enum' in schema:
        target = schema['x-canonical-enum']
        mapping = schema.get('x-value-map', {})
        if target not in defs or set(mapping) != set(schema.get('enum', [])) or set(mapping.values()) != set(defs.get(target, {}).get('enum', [])):
            errors.append(f'{path}: invalid canonical enum compatibility mapping')
    for name, child in schema.get('properties', {}).items():
        errors.extend(schema_errors(child, defs, path + '.' + name))
    for index, child in enumerate(c for c in schema_children(schema) if c not in schema.get('properties', {}).values()):
        errors.extend(schema_errors(child, defs, f'{path}[{index}]'))
    return errors


def accepts_type(value, kind):
    return {'object': isinstance(value, dict), 'array': isinstance(value, list),
            'string': isinstance(value, str), 'integer': type(value) is int or
            (type(value) is float and math.isfinite(value) and value.is_integer()),
            'number': type(value) in (int, float) and math.isfinite(value),
            'boolean': type(value) is bool, 'null': value is None}.get(kind, False)


def instance_errors(value, schema, defs, path='$', catalogs=None):
    errors = []
    if '$ref' in schema:
        target = schema['$ref'].removeprefix('#/$defs/')
        if target not in defs:
            return [f'{path}: undefined reference {target}']
        errors.extend(instance_errors(value, defs[target], defs, path, catalogs))
    for key in ('anyOf', 'oneOf', 'allOf'):
        if key in schema:
            outcomes = [instance_errors(value, child, defs, path, catalogs) for child in schema[key]]
            matches = sum(not outcome for outcome in outcomes)
            if (key == 'anyOf' and not matches) or (key == 'oneOf' and matches != 1) or (key == 'allOf' and matches != len(outcomes)):
                errors.append(f'{path}: {key} branch mismatch ({matches} matched)')
                if not matches and outcomes:
                    errors.extend(min(outcomes, key=len)[:3])
    if 'type' in schema:
        kinds = schema['type'] if isinstance(schema['type'], list) else [schema['type']]
        if not any(accepts_type(value, kind) for kind in kinds):
            return errors + [f'{path}: expected {schema["type"]}']
    def equal(first, second):
        if type(first) in (int, float) and type(second) in (int, float):
            return first == second
        return type(first) is type(second) and first == second

    if 'const' in schema and not equal(value, schema['const']):
        errors.append(f'{path}: incorrect discriminator')
    if 'enum' in schema and not any(equal(value, v) for v in schema['enum']):
        errors.append(f'{path}: invalid serialized enum value {value!r}')
    if isinstance(value, dict):
        for name in schema.get('required', []):
            if name not in value:
                errors.append(f'{path}.{name}: missing required field')
        properties = schema.get('properties', {})
        for name, item in value.items():
            if 'propertyNames' in schema:
                errors.extend(instance_errors(name, schema['propertyNames'], defs, path + '.<key>', catalogs))
            child = properties.get(name, schema.get('additionalProperties'))
            if child is False:
                errors.append(f'{path}.{name}: unexpected field')
            elif isinstance(child, dict):
                errors.extend(instance_errors(item, child, defs, path + '.' + name, catalogs))
    if isinstance(value, list):
        if 'items' in schema:
            for index, item in enumerate(value):
                errors.extend(instance_errors(item, schema['items'], defs, f'{path}[{index}]', catalogs))
        if schema.get('uniqueItems') and len(value) != len({json.dumps(v, sort_keys=True) for v in value}):
            errors.append(f'{path}: duplicate set entries')
        for key, test in [('minItems', len(value) < schema.get('minItems', 0)), ('maxItems', len(value) > schema.get('maxItems', math.inf))]:
            if test:
                errors.append(f'{path}: violates {key}')
    if type(value) in (int, float):
        if not math.isfinite(value):
            return errors + [f'{path}: number must be finite']
        for key, failed in [('minimum', value < schema.get('minimum', -math.inf)), ('maximum', value > schema.get('maximum', math.inf))]:
            if failed:
                errors.append(f'{path}: violates {key}')
        if 'multipleOf' in schema and Decimal(str(value)) % Decimal(str(schema['multipleOf'])):
            errors.append(f'{path}: violates multipleOf')
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0) or len(value) > schema.get('maxLength', math.inf):
            errors.append(f'{path}: violates string length')
        if schema.get('format') == 'date-time':
            try:
                if not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|\+00:00)', value):
                    raise ValueError('UTC required')
                datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                errors.append(f'{path}: expected RFC 3339 UTC instant')
        target = schema.get('x-reference', {})
        if catalogs and target:
            alternatives = [target['target'], *target.get('alternatives', [])]
            if target.get('kind') == 'content-member':
                alternatives = [name + '/' + target['member_path'] for name in alternatives]
            available = [catalogs[name] for name in alternatives if name in catalogs]
            if available and value not in set().union(*available):
                errors.append(f'{path}: unresolved content identity {value!r} in {alternatives}')
    return errors


def selected_values(data, selector):
    values = [data]
    for part in selector.split('/')[1:] if selector else []:
        next_values = []
        for value in values:
            if part == '*':
                next_values.extend(value.values() if isinstance(value, dict) else value)
            elif isinstance(value, dict) and part in value:
                next_values.append(value[part])
        values = next_values
    return values


def sample_errors(registry, root):
    defs = definitions(registry)
    sources = {}
    samples = []
    catalogs = {}
    member_targets = set()

    def collect_members(schema):
        identity = schema.get('x-reference', {})
        if identity.get('kind') == 'content-member':
            member_targets.add((identity['target'], identity['member_path']))
        for child in schema_children(schema):
            collect_members(child)

    for schema in defs.values():
        collect_members(schema)
    for binding in registry['sample_bindings']:
        path = binding['path']
        if path not in sources:
            sources[path] = json.loads((root / path).read_text())
        values = selected_values(sources[path], binding['selector'])
        samples.append((binding, values))
        ids = {v['id'] for v in values if isinstance(v, dict) and isinstance(v.get('id'), str)}
        if ids:
            catalogs.setdefault(binding['type'], set()).update(ids)
        for target, member_path in member_targets:
            if target == binding['type']:
                members = [member for value in values for member in selected_values(value, '/' + member_path)]
                flat = [item for member in members for item in (member if isinstance(member, list) else [member])]
                catalogs.setdefault(target + '/' + member_path, set()).update(item for item in flat if isinstance(item, str))
    errors = []
    for binding, values in samples:
        if not values:
            errors.append(f'{binding}: sample selector found no records')
        if binding['type'] not in defs:
            errors.append(f'{binding}: missing sample type')
            continue
        for index, value in enumerate(values):
            errors.extend(instance_errors(value, defs[binding['type']], defs,
                          f'{binding["path"]}{binding["selector"]}[{index}]', catalogs))
    return errors


def model_errors(registry, root):
    errors = []
    defs = definitions(registry)
    entries = {e['name']: e for e in registry['entries']}
    if registry['schema_dialect'] != DIALECT:
        errors.append('Unsupported schema dialect')
    if set(registry['shared_definitions']) & set(entries):
        errors.append('Shared definition shadows an inventory entry')
    if not registry['conventions'] or not registry['dependency_groups']:
        errors.append('Missing global conventions/dependency analysis')
    for group in registry['dependency_groups']:
        if not set(group['contracts']) <= set(entries) or not group['authority']:
            errors.append(f'{group["name"]}: invalid dependency group')
    for name, schema in defs.items():
        errors.extend(schema_errors(schema, defs, name))
    for name, entry in entries.items():
        actual = type_references(entry['definition']) - {name}
        if sorted(actual) != entry['references']:
            errors.append(f'{name}: inconsistent dependency metadata')
        if entry['reviewed_against'] != entry['evidence']:
            errors.append(f'{name}: stale per-contract evidence review')
        if not entry['responsibility'] or not entry['authority'] or not entry['modeling_notes']:
            errors.append(f'{name}: missing responsibility/authority/modeling rationale')
        blocked = bool(entry.get('review_issues'))
        if blocked != (entry['definition_status'] == 'Needs Decision') or blocked != (entry['definition_extent'] == 'Partial'):
            errors.append(f'{name}: decision status and definition extent disagree')
        if entry['category'] == 'Enum':
            members = entry.get('members', [])
            ids = [m['id'] for m in members]
            if len(ids) != len(set(ids)) or any(not m.get('description') for m in members):
                errors.append(f'{name}: duplicate or undescribed enum members')
            if not members and not blocked:
                errors.append(f'{name}: missing enum members or documented blocker')
            if entry.get('representation') in ('established', 'partially established'):
                if [m['value'] for m in members if 'value' in m] != entry['definition'].get('enum'):
                    errors.append(f'{name}: invalid enum reference/value projection')
                if entry.get('representation') == 'partially established' and (
                        not blocked or [m['id'] for m in members if 'value' not in m] != entry['definition'].get('x-members')):
                    errors.append(f'{name}: incomplete enum encoding requires a documented decision')
            elif entry['definition'].get('x-members') != ids or any('value' in m for m in members):
                errors.append(f'{name}: symbolic members cannot assign serialized values')
        if entry.get('previous_category') and entry['category'] != 'Schema':
            errors.append(f'{name}: invalid content identifier reclassification')
    for issue in registry['review_issues']:
        if issue.get('state') not in ('open', 'resolved') or not issue.get('alternatives') or not issue.get('impact'):
            errors.append(f'{issue["id"]}: incomplete decision record')
    graph = {name: type_references(schema, False) for name, schema in defs.items()}
    visited, active = set(), set()

    def visit(name):
        if name in active:
            errors.append(f'{name}: circular value containment; use identity reference')
            return
        if name in visited or name not in graph:
            return
        active.add(name)
        for target in graph[name]:
            visit(target)
        active.remove(name)
        visited.add(name)

    for name in graph:
        visit(name)
    reachable = set(entries)
    pending = list(entries)
    while pending:
        name = pending.pop()
        for target in type_references(defs[name]):
            if target in defs and target not in reachable:
                reachable.add(target)
                pending.append(target)
    for name in set(defs) - reachable:
        errors.append(f'{name}: orphaned shared definition')
    for binding in registry['sample_bindings']:
        path = root / binding['path']
        if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
            errors.append(f'{binding}: missing/nonlocal sample source')
    if not errors:
        errors.extend(sample_errors(registry, root))
    return errors


def review_report(registry):
    entries = registry['entries']
    initial = registry['initial_inventory_counts']
    feature_pages = sum(p['kind'] == 'Feature' for p in registry['pages'])
    lines = ['BRIARWAKE DATA MODEL DEFINITION AND REVIEW',
             'Generated from sources/data-inventory.json; edit that registry, then rebuild.',
             'Documentation contracts only; no gameplay/database/network implementation or balance certification.',
             '', 'A. DEFINITION COVERAGE',
             f'Original inventory: {initial["enums"]} enums, {initial["interfaces"]} interfaces, '
             f'{initial["schemas"]} schemas; all {initial["structures"]} examined.']
    for category in ('Enum', 'Interface', 'Schema'):
        selected = [e for e in entries if e['category'] == category]
        full = sum(e['definition_status'] == 'Fully Defined' for e in selected)
        lines.append(f'{category}: {len(selected)} total; {full} fully defined; {len(selected)-full} partial / Needs Decision.')
    lines.extend([f'Partial / Needs Decision structures: {sum(e["definition_extent"] == "Partial" for e in entries)}.',
                  f'Feature pages updated: {feature_pages} generated Data sections; feature pages reviewed: '
                  f'{feature_pages} ({len(registry["pages"])} source HTML pages total).',
                  '', 'B. DRY AND COMPATIBILITY AUDIT', *registry['audit_notes'],
                  '', 'C. CROSS-SYSTEM DEPENDENCY AND OWNERSHIP AUDIT'])
    for group in registry['dependency_groups']:
        lines.extend([group['name'] + ': ' + group['authority'], '  ' + ', '.join(group['contracts'])])
    lines.extend(['', 'D. CONVENTIONS AND ARCHITECTURE DECISIONS', *registry['conventions'],
                  '', 'E. OUTSTANDING AND RESOLVED DECISIONS'])
    for issue in registry['review_issues']:
        lines.extend([f'{issue["id"]} [{issue["state"]}]: {issue["question"]}',
                      '  Affected: ' + ', '.join(issue['entries']),
                      '  Sources: ' + ', '.join(issue['references']),
                      '  Alternatives: ' + ' | '.join(issue['alternatives']),
                      '  Recommendation: ' + (issue['recommendation'] or 'No evidence-supported preference.'),
                      '  Impact: ' + issue['impact']])
    lines.extend(['', 'F. REPEATABLE VALIDATION',
                  'python3 scripts/build_data_inventory.py --check',
                  'python3 validation/check_data_inventory.py',
                  "python3 -m unittest discover -s validation -p 'test_*.py'",
                  'python3 validation/run_checks.py',
                  'node validation/check_inventory_browser.mjs',
                  'Run outcomes are recorded in validation/report.json and data-inventory-browser-checks.json.',
                  'The standard-library checker validates the exact JSON Schema vocabulary used here and all bound shipped records.',
                  'It is not a general-purpose JSON Schema implementation; unsupported keywords fail closed.',
                  'x-members are symbolic, x-invariants require semantic/runtime checks, and Needs Decision shapes are partial.',
                  'Baseline before this task: 241 checks passed, zero failed; 11 inventory regression tests passed.',
                  '', 'G. FILE OWNERSHIP',
                  'sources/data-inventory.json: canonical definitions, shared types, evidence, ownership, dependencies, decisions.',
                  SCHEMA_PATH + ': generated JSON Schema 2020-12 $defs bundle; do not edit.',
                  'guide/data-inventory.html: generated definitions, coverage, decisions, evidence and feature backlinks.',
                  f'{feature_pages} feature Data sections, assets/search-index.js and data/manifest.json: existing generated ownership retained.',
                  'scripts/build_data_inventory.py and scripts/data_model.py: deterministic rendering and focused validation.',
                  'validation/: regression/browser checks, full check evidence and this generated review.',
                  '', 'PER-CONTRACT AUDIT: STATUS, DEPENDENCIES AND EVIDENCE'])
    for e in sorted(entries, key=lambda e: e['name'].casefold()):
        lines.extend([e['name'] + ': ' + e['definition_status'] + ' / ' + e['responsibility'],
                      '  Authority: ' + e['authority'],
                      '  References: ' + ', '.join(e['references']),
                      '  Reviewed sources: ' + ', '.join(e['reviewed_against'])])
    return '\n'.join(lines) + '\n'
