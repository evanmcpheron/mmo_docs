"""Regression tests for canonical contracts, compatibility and model boundaries."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_data_inventory import load_registry
from data_model import (definitions, instance_errors, model_errors, sample_errors,
                        schema_bundle, schema_errors, type_references)


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_registry()
        cls.defs = definitions(cls.registry)
        cls.entries = {e['name']: e for e in cls.registry['entries']}

    def rejected_model(self, registry, fragment):
        self.assertTrue(any(fragment in error for error in model_errors(registry, ROOT)), fragment)

    def test_all_original_identifiers_have_canonical_shapes(self):
        self.assertGreaterEqual(len(self.entries), self.registry['initial_inventory_counts']['structures'])
        self.assertTrue(all(e['definition'] and e['reviewed_against'] == e['evidence'] for e in self.entries.values()))
        self.assertEqual(set(self.defs), set(schema_bundle(self.registry)['$defs']))
        self.assertEqual([], model_errors(self.registry, ROOT))

    def test_every_shipped_variant_and_embedded_snapshot_matches(self):
        self.assertEqual([], sample_errors(self.registry, ROOT))
        abilities = json.loads((ROOT / 'data/abilities.json').read_text())
        for identifier in ('ability.arcanist.charge_lance', 'ability.beastmaster.guarding_fang', 'ability.totemist.calling_stone'):
            row = next(row for row in abilities if row['id'] == identifier)
            self.assertEqual([], instance_errors(row, self.defs['AbilityDefinition'], self.defs), identifier)

    def test_sample_reuse_detects_schema_binding_catalog_and_same_path_content_mutations(self):
        registry = {
            'shared_definitions': {},
            'entries': [{'name': 'Fixture', 'definition': {'type': 'integer', 'minimum': 1}}],
            'sample_bindings': [{'path': 'records.json', 'selector': '/*', 'type': 'Fixture'}],
        }
        with tempfile.TemporaryDirectory(dir=ROOT / '.git') as directory:
            root = Path(directory)
            records = root / 'records.json'
            records.write_text('[1]')
            self.assertEqual([], sample_errors(registry, root))
            schema = registry['entries'][0]['definition']
            schema['minimum'] = 2
            errors = sample_errors(registry, root)
            self.assertTrue(any('minimum' in error for error in errors))
            errors.clear()
            self.assertTrue(sample_errors(registry, root))
            schema['minimum'] = 1
            self.assertEqual([], sample_errors(registry, root))
            records.write_text('[0]')
            self.assertTrue(sample_errors(registry, root))
            records.write_text('[1]')
            self.assertEqual([], sample_errors(registry, root))
            registry['sample_bindings'][0]['selector'] = '/absent'
            self.assertTrue(any('no records' in error for error in sample_errors(registry, root)))
            registry['sample_bindings'][0]['selector'] = '/*'
            registry['sample_bindings'][0]['type'] = 'Missing'
            self.assertTrue(any('missing sample type' in error for error in sample_errors(registry, root)))

    def test_reused_sample_identity_checks_include_other_catalogs(self):
        registry = {
            'shared_definitions': {},
            'entries': [
                {'name': 'Target', 'definition': {'type': 'object', 'properties': {'id': {'type': 'string'}}}},
                {'name': 'Reference', 'definition': {'type': 'string', 'x-reference': {'target': 'Target'}}},
            ],
            'sample_bindings': [
                {'path': 'targets.json', 'selector': '/*', 'type': 'Target'},
                {'path': 'references.json', 'selector': '/*', 'type': 'Reference'},
            ],
        }
        with tempfile.TemporaryDirectory(dir=ROOT / '.git') as directory:
            root = Path(directory)
            (root / 'targets.json').write_text('[{"id":"known"}]')
            (root / 'references.json').write_text('["known"]')
            self.assertEqual([], sample_errors(registry, root))
            (root / 'targets.json').write_text('[{"id":"other"}]')
            self.assertTrue(any('unresolved content identity' in error for error in sample_errors(registry, root)))

    def test_canonical_reference_and_dependency_drift_are_rejected(self):
        registry = copy.deepcopy(self.registry)
        next(e for e in registry['entries'] if e['name'] == 'CharacterState')['definition']['properties']['health']['$ref'] = '#/$defs/MissingType'
        self.rejected_model(registry, 'undefined type reference')
        self.rejected_model(registry, 'inconsistent dependency metadata')

    def test_fixture_catalog_cannot_resolve_a_shipped_reference(self):
        registry = {
            'shared_definitions': {},
            'entries': [
                {'name': 'Target', 'definition': {'type': 'object', 'properties': {'id': {'type': 'string'}}}},
                {'name': 'Reference', 'definition': {'type': 'string', 'x-reference': {'target': 'Target'}}},
            ],
            'sample_bindings': [
                {'path': 'shipped.json', 'selector': '/targets/*', 'type': 'Target'},
                {'path': 'shipped.json', 'selector': '/references/*', 'type': 'Reference'},
                {'path': 'fixture.json', 'selector': '/targets/*', 'type': 'Target', 'catalog_scope': 'fixture'},
                {'path': 'fixture.json', 'selector': '/references/*', 'type': 'Reference', 'catalog_scope': 'fixture'},
            ],
        }
        with tempfile.TemporaryDirectory(dir=ROOT / '.git') as directory:
            root = Path(directory)
            shipped = root / 'shipped.json'
            shipped.write_text('{"targets":[{"id":"production"}],"references":["production"]}')
            (root / 'fixture.json').write_text(
                '{"targets":[{"id":"example"}],"references":["production","example"]}')
            self.assertEqual([], sample_errors(registry, root))
            shipped.write_text('{"targets":[{"id":"production"}],"references":["example"]}')
            errors = sample_errors(registry, root)
            self.assertEqual(1, len(errors), errors)
            self.assertIn('shipped.json', errors[0])
            self.assertIn('unresolved content identity', errors[0])
            for scope in ('', None, {}, 'Invalid Scope'):
                registry['sample_bindings'][2]['catalog_scope'] = scope
                self.assertTrue(any('invalid sample catalog scope' in error
                                    for error in sample_errors(registry, root)))

    def test_malformed_required_fields_and_untyped_containers_are_rejected(self):
        for schema in ({'type': 'object', 'properties': {}, 'required': ['absent'], 'additionalProperties': False},
                       {'type': 'array'}, {'type': 'object'}):
            self.assertTrue(schema_errors(schema, self.defs, 'fixture'))
        self.assertTrue(schema_errors({'type': 'number', 'minimim': 0}, self.defs, 'fixture'))

    def test_enum_members_and_compatibility_projection_cannot_diverge(self):
        registry = copy.deepcopy(self.registry)
        next(e for e in registry['entries'] if e['name'] == 'ItemGrade')['members'][0]['value'] = 'unsupported'
        self.rejected_model(registry, 'invalid enum reference/value projection')
        schema = copy.deepcopy(self.defs['ClassDefinition'])
        schema['properties']['armor']['x-value-map']['Cloth'] = 'plate'
        self.assertTrue(schema_errors(schema, self.defs, 'fixture'))
        self.assertTrue(instance_errors('legendary', self.defs['ItemGrade'], self.defs))

    def test_approved_string_encodings_cannot_drift(self):
        registry = copy.deepcopy(self.registry)
        next(e for e in registry['entries'] if e['name'] == 'QuestStatus')['members'][0]['value'] = 0
        self.rejected_model(registry, 'invalid enum reference/value projection')
        self.assertEqual([], instance_errors('accepted', self.defs['QuestStatus'], self.defs))
        self.assertTrue(instance_errors(0, self.defs['QuestStatus'], self.defs))
        self.assertTrue(instance_errors('Accepted', self.defs['QuestStatus'], self.defs))
        self.assertEqual('content reference', self.entries['CharacterClass']['responsibility'])
        self.assertNotIn('enum', self.defs['CharacterClass'])

    def test_optional_and_nullable_have_different_presence_rules(self):
        schema = self.defs['ability_command_v2']
        value = {'schema': 'ability_command_v2', 'session_epoch': 17, 'command_sequence': 403,
                 'character_id': 'character-example', 'ability_id': 'ability.arcanist.charge_lance',
                 'build_version': 8, 'content_version': '2.0.0-design', 'target_entity_id': 'entity-example',
                 'aim_point': None, 'aim_direction': None}
        self.assertEqual([], instance_errors(value, schema, self.defs))
        value['requested_charge_spend'] = None
        self.assertTrue(instance_errors(value, schema, self.defs))
        value.pop('requested_charge_spend')
        value.pop('aim_point')
        self.assertTrue(instance_errors(value, schema, self.defs))

    def test_dynamic_costs_and_item_operations_require_their_own_parameters(self):
        for value in ({}, {'mana_percent_base': 3}, {'mana_percent_base': 3, 'mana_percent_per_charge': 2, 'martial_energy_cost': 25}):
            self.assertTrue(instance_errors(value, self.defs['AbilityCostPolicy'], self.defs))
        self.assertEqual([], instance_errors({'mana_percent_base': 3, 'mana_percent_per_charge': 2}, self.defs['AbilityCostPolicy'], self.defs))
        self.assertTrue(instance_errors({'operation': 'EQUIP_BUDGET'}, self.defs['ItemEffectDefinition'], self.defs))

    def test_source_catalog_references_resolve(self):
        schema = {'$ref': '#/$defs/Id', 'x-reference': {'target': 'ItemDefinition', 'kind': 'content'}}
        self.assertTrue(instance_errors('missing', schema, self.defs, catalogs={'ItemDefinition': {'item.known'}}))
        self.assertEqual([], instance_errors('item.known', schema, self.defs, catalogs={'ItemDefinition': {'item.known'}}))

    def test_content_members_are_not_confused_with_enclosing_definition_ids(self):
        schema = self.defs['EncounterPhase']
        catalogs = {'EncounterDefinition': {'encounter.test'}, 'EncounterDefinition/phases': {'phase.opening'}}
        self.assertEqual([], instance_errors('phase.opening', schema, self.defs, catalogs=catalogs))
        self.assertTrue(instance_errors('encounter.test', schema, self.defs, catalogs=catalogs))

    def test_ownership_and_privacy_representations_remain_distinct(self):
        public = self.defs['EntitySnapshot']['properties']
        for forbidden in ('account_id', 'session', 'inventory', 'damage_ledger', 'loot_table_id'):
            self.assertNotIn(forbidden, public)
        self.assertNotIn('race_id', self.defs['CharacterAppearance']['properties'])
        self.assertEqual({'$ref': '#/$defs/CharacterLoadout', 'description': 'CharacterLoadoutRecord uses the canonical CharacterLoadout shape.'}, self.defs['CharacterLoadoutRecord'])
        for name in ('ArcanistCombatState', 'GravecallerCombatState', 'IronbodyCombatState'):
            self.assertNotIn('current', self.defs[name]['properties'])
            self.assertNotIn('health', self.defs[name]['properties'])

    def test_value_cycles_and_orphaned_helpers_are_rejected(self):
        registry = copy.deepcopy(self.registry)
        registry['shared_definitions']['Id'] = {'$ref': '#/$defs/CharacterState'}
        self.rejected_model(registry, 'circular value containment')
        registry = copy.deepcopy(self.registry)
        registry['shared_definitions']['UnusedHelper'] = {'type': 'string', 'description': 'Unused.'}
        self.rejected_model(registry, 'orphaned shared definition')

    def test_positive_quantities_finite_coordinates_and_precision(self):
        self.assertTrue(instance_errors(0, self.defs['ItemInstance']['properties']['quantity'], self.defs))
        self.assertTrue(instance_errors({'x': float('inf'), 'y': 0}, self.defs['Vector2'], self.defs))
        self.assertTrue(instance_errors(True, {'type': 'integer'}, self.defs))
        self.assertEqual([], instance_errors(1.0, {'type': 'integer'}, self.defs))
        self.assertEqual([], instance_errors(.123, self.defs['CombatAmount'], self.defs))
        self.assertTrue(instance_errors(.1234, self.defs['CombatAmount'], self.defs))


if __name__ == '__main__':
    unittest.main()
