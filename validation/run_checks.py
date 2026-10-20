"""Validate this design package, not a game-server implementation.

Run with Python 3.10+: python validation/run_checks.py
"""
from __future__ import annotations
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from check_data_inventory import inventory_errors
from check_development_roadmap import load as load_roadmap, roadmap_errors
from check_foundation import foundation_errors

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
checks: list[dict] = []

def load(name: str):
    return json.loads((DATA / name).read_text(encoding='utf-8'))

def check(name: str, condition: bool, detail: str = '') -> None:
    checks.append({'name': name, 'passed': bool(condition), 'detail': detail})

def legal(node: dict, allocation: dict, nodes: list[dict], level: int) -> bool:
    if node['min_character_level'] > level or allocation.get(node['id'], 0) >= node['max_ranks']:
        return False
    lower = sum(allocation.get(candidate['id'], 0) for candidate in nodes if candidate['tier'] < node['tier'])
    if lower < node['required_tree_points']:
        return False
    predecessors = node['prerequisite_any_talent_id']
    if predecessors and not any(allocation.get(identifier, 0) >= node['prerequisite_min_rank'] for identifier in predecessors):
        return False
    group = node['exclusive_group']
    if group and any(other['id'] != node['id'] and other['exclusive_group'] == group and allocation.get(other['id'], 0) for other in nodes):
        return False
    if node['requires_transformation'] and not any(other['tier'] == 2 and other['exclusive_group'] and allocation.get(other['id'], 0) for other in nodes):
        return False
    return True

def allocate(nodes: list[dict], level: int, budget: int, route: int | None = None) -> dict:
    allocation: dict[str, int] = {}
    def add(node):
        if sum(allocation.values()) < budget and legal(node, allocation, nodes, level):
            allocation[node['id']] = allocation.get(node['id'], 0) + 1
            return True
        return False
    if route is not None:
        # Construct one legal route to a capstone before filling remaining ranks.
        for tier in range(2, 7):
            target = [node for node in nodes if node['tier'] == tier and node['exclusive_group']]
            selected = target[route % len(target)] if target else next(node for node in nodes if node['tier'] == tier)
            for _ in range(100):
                if legal(selected, allocation, nodes, level):
                    add(selected)
                    break
                available = [node for node in nodes if node['tier'] < tier and legal(node, allocation, nodes, level)]
                if not available:
                    break
                # Ensure a predecessor in the immediately previous tier, then build the threshold.
                available.sort(key=lambda node: (0 if node['tier'] == tier - 1 and allocation.get(node['id'], 0) == 0 else 1, node['tier'], node['position']))
                if not add(available[0]):
                    break
    for _ in range(250):
        if sum(allocation.values()) >= budget:
            break
        available = [node for node in nodes if legal(node, allocation, nodes, level)]
        if not available:
            break
        available.sort(key=lambda node: (0 if node['tier'] == 2 and node['exclusive_group'] else 1, node['tier'], node['position']))
        add(available[0])
    return allocation

def validate_allocation(nodes: list[dict], allocation: dict, level: int, budget: int) -> bool:
    groups = Counter()
    for node in nodes:
        rank = allocation.get(node['id'], 0)
        if not rank:
            continue
        if not isinstance(rank, int) or not 1 <= rank <= node['max_ranks'] or node['min_character_level'] > level:
            return False
        if sum(allocation.get(other['id'], 0) for other in nodes if other['tier'] < node['tier']) < node['required_tree_points']:
            return False
        if node['prerequisite_any_talent_id'] and not any(allocation.get(identifier, 0) >= node['prerequisite_min_rank'] for identifier in node['prerequisite_any_talent_id']):
            return False
        if node['exclusive_group']:
            groups[node['exclusive_group']] += 1
        if node['requires_transformation'] and not any(other['tier'] == 2 and other['exclusive_group'] and allocation.get(other['id'], 0) for other in nodes):
            return False
    return sum(allocation.values()) == budget and max(groups.values(), default=0) <= 1

catalog = load('character_catalog.json')
abilities = catalog['abilities']; talents = catalog['talents']; races = catalog['races']
classes = catalog['classes']; specs = catalog['specializations']; owners = classes + specs
ability_by_id = {item['id']: item for item in abilities}
owner_ids = {owner['id'] for owner in owners}
for name, values in [('classes', classes), ('specializations', specs), ('abilities', abilities), ('talents', talents), ('races', races), ('recipes', load('recipes.json')), ('materials', load('materials.json')), ('profession_talents', load('profession_talents.json'))]:
    check(f'Unique identifiers: {name}', len({value['id'] for value in values}) == len(values), f'{len(values)} records')
check('Expected inherited class/spec/ability counts', (len(classes), len(specs), len(abilities)) == (12, 37, 330))
check('49 expanded character trees', len(owners) == 49 and all(sum(node['owner_id'] == owner['id'] for node in talents) == 36 for owner in owners))
check('Talents reference valid owners and abilities', all(node['owner_id'] in owner_ids and all(identifier in ability_by_id for identifier in node['required_ability_ids']) for node in talents))
check('Ability requirements agree with node unlocks', all(all(ability_by_id[identifier]['level'] <= node['min_character_level'] for identifier in node['required_ability_ids']) for node in talents))
check('All original talent IDs traceable', sum(node.get('source_version') == 'v1' for node in talents) == 882)
for owner in owners:
    nodes = [node for node in talents if node['owner_id'] == owner['id']]
    ids = {node['id'] for node in nodes}
    check(f"Tree structure: {owner['id']}", all(sum(node['tier'] == tier for node in nodes) == 6 for tier in range(1, 7)) and all(all(identifier in ids for identifier in node['prerequisite_any_talent_id']) for node in nodes))
    selectable = sum(node['max_ranks'] for node in nodes if not node['exclusive_group']) + 2
    check(f"Selectable rank capacity: {owner['id']}", selectable == 92)

capacity_failures = []
for owner in owners:
    nodes = [node for node in talents if node['owner_id'] == owner['id']]
    for level in range(1, 61):
        budget = level - 1 if owner in classes or level >= 10 else 0
        allocation = allocate(nodes, level, budget)
        if not validate_allocation(nodes, allocation, level, budget):
            capacity_failures.append([owner['id'], level, budget, sum(allocation.values())])
check('Legal allocation at every level for all 49 trees', not capacity_failures, f'2,940 owner/level cases; failures: {capacity_failures}')
sample_builds = []
for owner in owners:
    nodes = [node for node in talents if node['owner_id'] == owner['id']]
    for route in [0, 1]:
        allocation = allocate(nodes, 60, 59, route)
        has_capstone = any(node['tier'] == 6 and node['exclusive_group'] and allocation.get(node['id'], 0) for node in nodes)
        check(f"Capstone allocation: {owner['id']} route {route + 1}", validate_allocation(nodes, allocation, 60, 59) and has_capstone)
        sample_builds.append({'owner_id': owner['id'], 'route': route + 1, 'level': 60, 'points': 59, 'allocation': allocation, 'status': 'structural_example_not_optimized_or_playtested'})
(DATA / 'allocation_examples.json').write_text(json.dumps(sample_builds, indent=2) + '\n')
progression = load('progression.json')
check('Two points every level-up; 118 at cap', all(row['total_points'] == 2 * (row['level'] - 1) and row['class_points'] == row['specialization_points'] == row['level'] - 1 for row in progression) and progression[-1]['total_points'] == 118)
check('Specialization points bank before level 10', all(row['spendable_specialization_points'] == (row['level'] - 1 if row['level'] >= 10 else 0) for row in progression))
check('11 distinct races; Human on both sides; Ogre absent', len(races) == 11 and sum(len(race['factions']) for race in races) == 12 and next(race for race in races if race['id'] == 'human')['factions'] == ['good', 'evil'] and all(race['id'] != 'ogre' for race in races))
check('Racial modifiers sum to zero; same combat capsule', all(sum(race['starting_attribute_modifiers'].values()) == 0 and race['combat_collision_radius'] == .30 for race in races))
check('Faction-exclusive classes exact', all(character['factions'] == (['good'] if character['id'] in ['paladin', 'cleric'] else ['evil'] if character['id'] in ['necromancer', 'warlock'] else ['good', 'evil']) for character in classes))
coverage = {side: dict(Counter(spec['role'] for spec in specs if side in spec['factions'])) for side in ['good', 'evil']}
check('Both factions have tank/healer/DPS specializations', all(all(coverage[side].get(role, 0) > 0 for role in ['tank', 'healer', 'dps']) for side in coverage), str(coverage))
check('Healers use Mana as sustained resource', all(spec['sustained_resource'] == 'mana' for spec in specs if spec['role'] == 'healer'))
check('Starting primary attribute defined for all classes', all(character.get('starting_primary_attribute') in ['strength', 'agility', 'intellect'] for character in classes))
profiles = load('execution_profiles.json')
check('Ability profiles and timing values valid', all(ability['profile_id'] in profiles and all(isinstance(ability['execution'][key], (int, float)) and math.isfinite(ability['execution'][key]) and ability['execution'][key] >= 0 for key in ['cast_seconds','cooldown_seconds','mana_cost_percent','duration_seconds']) for ability in abilities))
check('All 37 specializations have contrasting playstyle contracts', all(all(spec['playstyle'].get(key) for key in ['loop', 'route_a', 'route_b', 'tradeoff', 'resource_contract']) for spec in specs))
professions = load('professions.json'); profession_talents = load('profession_talents.json'); recipes = load('recipes.json'); materials = load('materials.json'); items = load('item_examples.json')
check('16 professions: 9 manufacture, 4 gather, 3 life', Counter(prof['category'] for prof in professions) == {'manufacturing': 9, 'gathering': 4, 'life_skill': 3})
check('Profession mastery remains independent', len(profession_talents) == 240 and all(sum(node['max_ranks'] for node in profession_talents if node['profession_id'] == prof['id']) == 45 and prof['mastery_points'] == 30 for prof in professions))
check('Manufacturing recipe coverage in all six bands', all(sum(recipe['profession_id'] == prof['id'] and recipe['band'] == band for recipe in recipes) >= 4 for prof in professions if prof['category'] == 'manufacturing' for band in range(1, 7)))
material_ids = {material['id'] for material in materials}; item_ids = {item['id'] for item in items}
check('Recipe inputs and outputs resolve', all(recipe['output_item_id'] in item_ids and all(ingredient['material_id'] in material_ids and isinstance(ingredient['quantity'], int) and ingredient['quantity'] > 0 for ingredient in recipe['inputs']) for recipe in recipes))
check('Recipe skill/level/output bounds', all(1 <= recipe['required_skill'] <= 300 and 1 <= recipe['customer_level_target'] <= 60 and recipe['output_quantity'] >= 1 for recipe in recipes))
check('Every recipe targets a user inside its own level band', all([1,10,20,30,40,50][recipe['band']-1] <= recipe['customer_level_target'] <= [9,19,29,39,49,60][recipe['band']-1] for recipe in recipes))
check('All representative item outputs have numerical operations', all(item['effect']['operation'] != 'CONFIGURED_ITEM_OR_SERVICE' and not item['effect'].get('configuration_required', False) for item in items))
check('Representative equipment respects attribute and enhancement budget', all(sum(item['equipment']['attributes'].values()) + item['equipment']['reserved_enhancement_budget'] <= item['equipment']['total_attribute_budget'] + .00001 for item in items if 'equipment' in item))
check('Craft result binding matches output item definition', all(next(item['binding'] for item in items if item['id'] == recipe['output_item_id']) == recipe['binding_result'] for recipe in recipes))
check('Bound components are customer-owned in all challenge commissions', all(any(ingredient['material_id'] == 'material.challenge_core' and ingredient.get('must_be_customer_owned') for ingredient in recipe['inputs']) and recipe['binding_result'] == 'character_bound' for recipe in recipes if recipe['grade'] == 'challenge'))
check('Bard performance instruments occupy equipment slots', all(item['kind'] == 'equipment' for item in items if item['id'].startswith('item.woodworking.') and 'Performance instrument' in item['name']))
check('Level 60 combat power example', math.isclose(20 + 3 * 60 + 1.5 * (10 + 3 * 59 + 180), 750.5))
check('Ward and critical arithmetic', math.isclose(1.1 * 750.5 * (1 - 800 / (800 + 1600)), 550.3666666666667) and math.isclose(1.5 * 1.1 * 750.5 * (1 - 800 / (800 + 1600)), 825.55))
check('Tank and non-tank health arithmetic', math.isclose((80 + 32 * 60 + 10 * 268) * 1.3, 6084) and 80 + 32 * 60 + 10 * 268 == 4680)
check('Race influence dilutes', 3 / 750.5 < .005 and .078 < 3 / 38 < .080)
check('Independent mitigation multiplies', math.isclose(1 - .7 * .8, .44) and math.isclose(1 - .7 * .8 * .9, .496))
check('Haste cannot lower GCD below one second', all(max(1, 1.25 / (1 + haste)) >= 1 for haste in [0,.1,.2,.3]))
check('Enhancements and item allocation conserve budget', .45 + .35 + .20 == 1 and math.isclose(.92 + .08, 1))

class Document(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids = []; self.references = []
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if 'id' in values: self.ids.append(values['id'])
        for attr in ['href', 'src']:
            if values.get(attr): self.references.append(values[attr])
html_files = list(ROOT.rglob('*.html')); documents = {}; link_errors = []
for file in html_files:
    document = Document(); text = file.read_text(encoding='utf-8'); document.feed(text); documents[file.resolve()] = document
    if len(document.ids) != len(set(document.ids)): link_errors.append(f'{file.relative_to(ROOT)}: duplicate IDs')
    if re.search(r'\{\{[A-Z_]+\}\}', text): link_errors.append(f'{file.relative_to(ROOT)}: unresolved template token')
for file, document in documents.items():
    for reference in document.references:
        parsed = urlsplit(reference)
        if parsed.scheme or reference.startswith('//'): continue
        target = (file.parent / unquote(parsed.path)).resolve() if parsed.path else file
        if not target.exists(): link_errors.append(f'{file.relative_to(ROOT)}: missing {reference}'); continue
        if parsed.fragment and target.suffix == '.html' and unquote(parsed.fragment) not in documents[target].ids:
            link_errors.append(f'{file.relative_to(ROOT)}: missing anchor {reference}')
if html_files:
    check('Local HTML links, anchors and template completion', not link_errors, f'{len(html_files)} HTML pages; errors: {link_errors[:20]}')
    search_source = (ROOT / 'assets' / 'search-index.js').read_text()
    search_records = json.loads(search_source.removeprefix('window.SEARCH_INDEX=').strip().removesuffix(';'))
    search_errors = []
    for record in search_records:
        address = urlsplit(record['url'])
        target = (ROOT / address.path).resolve()
        if target not in documents or (address.fragment and address.fragment not in documents[target].ids):
            search_errors.append(record['url'])
    check('Global search destinations and anchors', not search_errors, f'{len(search_records)} indexed destinations; errors: {search_errors[:10]}')
else:
    check('HTML generation complete', False, 'Run again after generating the website.')
inventory_registry, data_inventory_errors = inventory_errors()
check('Data inventory coverage, evidence and generated output', not data_inventory_errors,
      f"{len(inventory_registry['entries'])} structures; errors: {data_inventory_errors[:20]}")
development_roadmap = load_roadmap()
development_roadmap_errors = roadmap_errors(development_roadmap)
check('Development roadmap dependencies, evidence, coverage and generated progress', not development_roadmap_errors,
      f"{len(development_roadmap['epics'])} epics; errors: {development_roadmap_errors[:20]}")
native_foundation_errors = foundation_errors(roadmap=development_roadmap)
check('Independent Unreal C++ foundation and supplied plugin prerequisites', not native_foundation_errors,
      str(native_foundation_errors))
counts = Counter(ability['content_status'] for ability in abilities)
talent_counts = Counter(node['binding_status'] for node in talents)
report = {'generated_at_utc': datetime.now(timezone.utc).isoformat(), 'package_version': catalog['version'], 'checks_passed': sum(check['passed'] for check in checks), 'checks_failed': sum(not check['passed'] for check in checks), 'checks': checks, 'level_allocation_cases': 2940, 'sample_capstone_allocations': len(sample_builds), 'faction_role_coverage': coverage, 'readiness': {'ability_status_counts': dict(counts), 'talent_status_counts': dict(talent_counts), 'representative_item_configuration_required': sum(item.get('effect', {}).get('configuration_required', False) for item in items), 'gameplay_balance_tested': False, 'database_integration_tested': False, 'network_capacity_tested': False}, 'html_page_count': len(html_files)}
(ROOT / 'validation' / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key: report[key] for key in ['checks_passed','checks_failed','level_allocation_cases','sample_capstone_allocations','html_page_count']}, indent=2))
for result in checks:
    if not result['passed']: print('FAIL:', result['name'], result['detail'])
raise SystemExit(1 if report['checks_failed'] else 0)
