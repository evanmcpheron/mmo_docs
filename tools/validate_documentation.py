#!/usr/bin/env python3
"""Check the present manual's links, registry and source-evidence invariants."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
ROOT = Path(__file__).resolve().parents[1]

class PageParser(HTMLParser):

    def __init__(self) -> None:
        super().__init__()
        self.ids = []
        self.links = []
        self.resources = []
        self.heading_count = 0

    def handle_starttag(self, tag: str, attributes: list) -> None:
        attrs = dict(attributes)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'h1':
            self.heading_count += 1
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        if tag in {'script', 'img', 'iframe', 'source'} and 'src' in attrs:
            self.resources.append(attrs['src'])
        if tag == 'link' and 'href' in attrs:
            self.resources.append(attrs['href'])

def registry_errors(assets: list[dict]) -> list[str]:
    errors = []
    required = {'name', 'type', 'parent/native_base', 'exact_game_path_or_source_path', 'first_phase', 'first_active_phase', 'owner', 'lifetime', 'replication', 'persistence', 'status', 'dependencies', 'reverse_users', 'doc_path', 'work_kind', 'consumers'}
    for field in ['name', 'exact_game_path_or_source_path', 'doc_path']:
        values = [asset.get(field) for asset in assets]
        for value, count in Counter(values).items():
            if count > 1:
                errors.append(f'Duplicate {field}: {value}')
    by_name = {asset.get('name'): asset for asset in assets}
    for asset in assets:
        name = asset.get('name', 'unnamed')
        missing = required - set(asset)
        if missing:
            errors.append(f'{name}: missing fields {sorted(missing)}')
            continue
        if not 0 <= asset['first_phase'] <= asset['first_active_phase'] <= 31:
            errors.append(f'{name}: invalid phase range')
        if not asset['owner'] or not asset['consumers']:
            errors.append(f'{name}: missing owner or consumer contract')
        if asset['status'] not in {'design', 'fixture', 'art-present', 'blocked', 'verified'}:
            errors.append(f'{name}: unknown status')
        if asset['status'] == 'verified' and (not asset.get('evidence')):
            errors.append(f'{name}: verified without evidence')
        if not asset['doc_path'].startswith('assets/'):
            errors.append(f'{name}: invalid documentation folder')
        for dependency in asset['dependencies']:
            if dependency not in by_name:
                errors.append(f'{name}: unknown dependency {dependency}')
            elif by_name[dependency]['first_phase'] > asset['first_phase']:
                errors.append(f'{name}: later dependency {dependency}')
        reverse = sorted((asset['name'] for asset in assets if name in asset.get('dependencies', [])))
        if sorted(asset['reverse_users']) != reverse:
            errors.append(f'{name}: reverse dependency mismatch')
    visiting = set()
    visited = set()

    def visit(name: str) -> None:
        if name in visiting:
            errors.append(f'Dependency cycle at {name}')
            return
        if name in visited or name not in by_name:
            return
        visiting.add(name)
        for dependency in by_name[name].get('dependencies', []):
            visit(dependency)
        visiting.remove(name)
        visited.add(name)
    for name in by_name:
        visit(name)
    return errors

def validate(root: Path) -> dict:
    errors = []
    parsed = {}
    graph = {}
    local_links = 0
    external_links = 0
    html_files = sorted(root.rglob('*.html'))
    for path in html_files:
        parser = PageParser()
        text = path.read_text(encoding='utf-8')
        parser.feed(text)
        parsed[path.resolve()] = parser
        if parser.heading_count != 1:
            errors.append(f'{path.relative_to(root)}: expected one h1')
        duplicates = [identifier for identifier, count in Counter(parser.ids).items() if count > 1]
        if duplicates:
            errors.append(f'{path.relative_to(root)}: duplicate IDs {duplicates}')
        if '[[' in text or ']]' in text:
            errors.append(f'{path.relative_to(root)}: unresolved authored token')
    for path, parser in parsed.items():
        graph[path] = set()
        for url, is_resource in [(url, False) for url in parser.links] + [(url, True) for url in parser.resources]:
            parts = urlsplit(url)
            if parts.scheme or parts.netloc:
                external_links += 1
                if is_resource:
                    errors.append(f'{path.relative_to(root)}: external runtime resource {url}')
                continue
            local_links += 1
            if not url or url == '#':
                errors.append(f'{path.relative_to(root)}: empty link')
                continue
            destination = (path.parent / unquote(parts.path)).resolve() if parts.path else path
            if not destination.is_relative_to(root.resolve()):
                errors.append(f'{path.relative_to(root)}: link escapes package {url}')
                continue
            if not destination.exists():
                errors.append(f'{path.relative_to(root)}: missing target {url}')
                continue
            if destination in parsed:
                graph[path].add(destination)
                if parts.fragment and unquote(parts.fragment) not in parsed[destination].ids:
                    errors.append(f'{path.relative_to(root)}: missing fragment {url}')
    home = (root / 'index.html').resolve()
    reachable = set()
    pending = [home]
    while pending:
        path = pending.pop()
        if path in reachable:
            continue
        reachable.add(path)
        pending.extend(graph.get(path, set()) - reachable)
    orphans = set(parsed) - reachable
    errors.extend(('Orphan HTML page: ' + str(path.relative_to(root)) for path in sorted(orphans)))
    assets = json.loads((root / 'sources/current-asset-manifest.json').read_text(encoding='utf-8'))['assets']
    errors.extend(registry_errors(assets))
    pages = json.loads((root / 'sources/manual-pages.json').read_text(encoding='utf-8'))['pages']
    authored_paths = {page['path'] for page in pages}
    actual_paths = {str(path.relative_to(root)).replace('\\', '/') for path in html_files}
    if authored_paths != actual_paths:
        errors.append('Canonical page registry differs from generated HTML set')
    for asset in assets:
        if not (root / asset['doc_path']).exists():
            errors.append('Missing asset page: ' + asset['name'])
    order = json.loads((root / 'sources/phase-creation-order.json').read_text(encoding='utf-8'))['order']
    if len(order) != len(assets) or set(order) != {asset['name'] for asset in assets}:
        errors.append('Creation order does not contain exactly the registered assets')
    position = {name: index for index, name in enumerate(order)}
    for asset in assets:
        for dependency in asset['dependencies']:
            if position.get(dependency, 10 ** 9) >= position.get(asset['name'], -1):
                errors.append(f"Invalid creation order: {dependency} before {asset['name']}")
    edges = json.loads((root / 'sources/dependency-edges.json').read_text(encoding='utf-8'))['edges']
    if {(edge['asset'], edge['requires']) for edge in edges} != {(asset['name'], dependency) for asset in assets for dependency in asset['dependencies']}:
        errors.append('Dependency edge source is stale')
    evidence = json.loads((root / 'sources/verification.json').read_text(encoding='utf-8'))
    digest = hashlib.sha256((root / 'sources/MASTER_PROMPT.original.md').read_bytes()).hexdigest()
    if digest != evidence['brief_sha256']:
        errors.append('Original brief hash changed')
    forbidden = {'.uasset', '.umap', '.uproject', '.cpp', '.h', '.dll', '.so', '.exe', '.png', '.jpg', '.wav', '.mp3', '.zip'}
    for path in root.rglob('*'):
        if path.is_file() and path.suffix.lower() in forbidden:
            errors.append('Unexpected game/art/binary payload: ' + str(path.relative_to(root)))
    for path in (root / 'site').glob('*.js'):
        if re.search('\\bfetch\\s*\\(', path.read_text(encoding='utf-8')):
            errors.append('Offline runtime fetch is not allowed: ' + str(path.relative_to(root)))
    with (root / 'sources/source-art-inventory.csv').open(newline='', encoding='utf-8') as inventory_file:
        source_art_count = sum((1 for row in csv.DictReader(inventory_file) if row.get('relative_path')))
    return {'status': 'pass' if not errors else 'fail', 'scope': 'Internal integrity of present documentation only; not full editorial coverage or game validation', 'html_pages': len(html_files), 'registered_assets': len(assets), 'local_link_occurrences_checked': local_links, 'external_reference_occurrences_not_network_checked': external_links, 'orphan_pages': len(orphans), 'source_art_files_inventoried': source_art_count, 'errors': errors, 'game_runtime': 'not_run'}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    report = validate(args.root)
    output = args.root / 'verification/validation.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'pass' else 1
if __name__ == '__main__':
    raise SystemExit(main())
