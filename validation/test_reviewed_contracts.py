"""Check invalid boundary payloads and the reviewed ownership/privacy contracts."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_data_inventory import load_registry, validate_registry
from data_model import command_targeting_errors, definitions, instance_errors, model_errors


class ReviewedContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_registry()
        cls.defs = definitions(cls.registry)

    def errors(self, name, value):
        return instance_errors(value, self.defs[name], self.defs)

    def command(self, **inputs):
        return {'schema': 'ability_command_v2', 'session_epoch': 17, 'command_sequence': 403,
                'ability_id': 'ability.example', 'build_version': 8, 'content_version': '2.1.0-design',
                'target_entity_id': None, 'aim_point': None, 'aim_direction': None, **inputs}

    def policy(self, mode, kind):
        return {'mode': mode, 'input_kind': kind, 'relation': 'enemy', 'range_units': 8,
                'radius_units': 0, 'target_cap': 1, 'floor_policy_id': 'same_floor',
                'line_of_sight_policy_id': 'unobstructed', 'revalidate': []}

    def test_every_existing_mode_has_exact_input_rules(self):
        expected = {
            'channel_friendly': ['entity'], 'cone': ['direction'], 'dash_point': ['point'],
            'dash_target': ['entity'], 'enemy_channel': ['entity'], 'enemy_line': ['direction'],
            'enemy_melee': ['entity'], 'enemy_projectile': ['entity'], 'enemy_target': ['entity'],
            'friendly': ['entity'], 'friendly_chain': ['entity'], 'friendly_cone': ['direction'],
            'friendly_dash': ['entity'], 'ground': ['point'], 'passive': ['none'],
            'pet_command': ['entity', 'none'], 'self': ['none'], 'self_aoe': ['none'],
            'summon': ['entity', 'point', 'none'], 'summon_static': ['point'], 'toggle': ['none'],
        }
        self.assertEqual(set(expected), set(self.defs['TargetMode']['enum']))
        for mode, allowed in expected.items():
            for kind in ('entity', 'point', 'direction', 'none'):
                with self.subTest(mode=mode, kind=kind):
                    self.assertEqual(kind not in allowed, bool(self.errors('AbilityTargetingPolicy', self.policy(mode, kind))))

    def test_commands_reject_missing_ambiguous_and_wrong_mode_inputs(self):
        entity_command = self.command(target_entity_id='visible-enemy')
        self.assertEqual([], command_targeting_errors(entity_command, self.policy('enemy_target', 'entity'), self.defs))
        self.assertEqual([], self.errors('ability_command_v2', {**entity_command, 'character_id': 'owner'}))
        for field in ('target_entity_id', 'aim_point', 'aim_direction'):
            invalid = copy.deepcopy(entity_command)
            invalid.pop(field)
            self.assertTrue(self.errors('ability_command_v2', invalid), field)
        self.assertTrue(self.errors('ability_command_v2', self.command(target_entity_id='enemy', aim_direction={'x': 1, 'y': 0})))
        self.assertTrue(command_targeting_errors(entity_command, self.policy('ground', 'point'), self.defs))
        self.assertTrue(command_targeting_errors(self.command(), self.policy('passive', 'none'), self.defs))
        self.assertTrue(self.errors('ability_command_v2', {**entity_command, 'requested_charge_spend': 0}))

    def test_directions_are_nonzero_and_wire_points_cannot_select_world_scope(self):
        self.assertEqual([], command_targeting_errors(self.command(aim_direction={'x': 2, 'y': -3}), self.policy('cone', 'direction'), self.defs))
        for vector in ({'x': 0, 'y': 0}, {'x': float('nan'), 'y': 1}, {'x': 1, 'y': float('inf')}):
            self.assertTrue(self.errors('ability_command_v2', self.command(aim_direction=vector)))
        point = {'zone_id': 'other-zone', 'instance_id': 'other-instance', 'floor_id': 'other-floor', 'position': {'x': 1, 'y': 2}}
        self.assertTrue(self.errors('ability_command_v2', self.command(aim_point=point)))
        self.assertEqual([], self.errors('TargetSelection', {'mode': 'ground', 'entity_id': None, 'aim_point': point, 'aim_direction': None}))
        self.assertTrue(self.errors('TargetSelection', {'mode': 'ground', 'entity_id': None, 'aim_point': {'x': 1, 'y': 2}, 'aim_direction': None}))
        self.assertEqual([], instance_errors(None, self.defs['CombatHudState']['properties']['target'], self.defs))

    def test_equip_requires_one_item_slot_and_concurrency_versions(self):
        value = {'operation': {'operation_key': 'equip-once'}, 'transfer': 'equip',
                 'items': [{'item': {'item_id': 'sword', 'expected_version': 4}, 'quantity': 1}],
                 'destination_container_id': 'owner-equipment', 'expected_destination_version': 5,
                 'slot': 'main_hand', 'expected_equipment_version': 9}
        self.assertEqual([], self.errors('InventoryOperationRequest', value))
        for field in ('slot', 'expected_equipment_version', 'expected_destination_version'):
            invalid = copy.deepcopy(value)
            invalid.pop(field)
            self.assertTrue(self.errors('InventoryOperationRequest', invalid), field)
        invalid = copy.deepcopy(value)
        invalid['items'][0]['quantity'] = 2
        self.assertTrue(self.errors('InventoryOperationRequest', invalid))
        invalid = copy.deepcopy(value)
        invalid['items'].append(copy.deepcopy(value['items'][0]))
        self.assertTrue(self.errors('InventoryOperationRequest', invalid))
        self.assertTrue(self.errors('InventoryOperationRequest', {**value, 'transfer': 'bank'}))

    def test_guild_variants_reject_unrelated_fields_and_permission_claims(self):
        invite = {'schema': 'guild_command_v1', 'operation': {'operation_key': 'invite-once'},
                  'guild_id': 'guild', 'expected_version': 4, 'permission': 'invite',
                  'recipient_character_id': 'recipient'}
        self.assertEqual([], self.errors('GuildCommand', invite))
        self.assertTrue(self.errors('GuildCommand', {**invite, 'rank_policy': {}}))
        response = {'schema': 'guild_command_v1', 'operation': {'operation_key': 'accept-once'},
                    'guild_id': 'guild', 'invitation_action': 'accept',
                    'invitation_id': 'invitation', 'expected_invitation_version': 2}
        self.assertEqual([], self.errors('GuildCommand', response))
        self.assertTrue(self.errors('GuildCommand', {**response, 'permission': 'invite'}))
        response.pop('expected_invitation_version')
        self.assertTrue(self.errors('GuildCommand', response))
        bank = {'schema': 'guild_command_v1', 'operation': {'operation_key': 'deposit-once'},
                'guild_id': 'guild', 'expected_version': 4, 'permission': 'bank_deposit',
                'bank_transfer': {'operation': {'operation_key': 'transfer-once'}, 'transfer': 'bank',
                                  'items': [{'item': {'item_id': 'ore', 'expected_version': 3}, 'quantity': 2}],
                                  'destination_container_id': 'guild-bank', 'expected_destination_version': 2}}
        self.assertEqual([], self.errors('GuildCommand', bank))
        bank['bank_transfer']['transfer'] = 'salvage'
        self.assertTrue(self.errors('GuildCommand', bank))
        party = {'schema': 'party_command_v1', 'command': {'session_epoch': 1, 'command_sequence': 2},
                 'operation': {'kind': 'decline_invitation', 'invitation_id': 'invitation', 'expected_invitation_version': 2}}
        self.assertEqual([], self.errors('PartyCommand', party))

    def test_public_results_redact_hidden_sources_and_reject_internal_fields(self):
        result = {'action_id': 'recipient-action', 'source_entity_id': None, 'target_entity_id': 'recipient',
                  'school': 'physical', 'critical': False, 'effective_damage': 12, 'effective_healing': 0}
        self.assertEqual([], self.errors('PublicCombatResult', result))
        for field in ('raw_amount', 'mitigated_amount', 'overkill', 'absorbs_consumed', 'resource_balance'):
            self.assertTrue(self.errors('PublicCombatResult', {**result, field: 12}), field)
        self.assertTrue(self.errors('CombatResult', result))

    def test_summon_category_cannot_silently_change_capacity_cost(self):
        value = {'id': 'summon.bonewright', 'kind': 'specialized_mobile', 'capacity_cost': 2,
                 'lifetime_seconds': 0, 'aggregate_budget_fraction': .5,
                 'inheritance_policy_id': 'owner-budget', 'cleanup_policy_id': 'owner-cleanup'}
        self.assertEqual([], self.errors('SummonDefinition', value))
        self.assertTrue(self.errors('SummonDefinition', {**value, 'capacity_cost': 4}))
        self.assertTrue(self.errors('SummonDefinition', {**value, 'kind': 'elite_companion'}))
        self.assertEqual([], self.errors('SummonDefinition', {**value, 'kind': 'elite_companion', 'capacity_cost': 4}))

    def test_cleanup_flags_compose_without_an_ambiguous_single_enum(self):
        flags = {'cleanup_on_death': True, 'cleanup_on_logout': True, 'checkpoint_for_transfer': True}
        self.assertEqual([], self.errors('StatusPersistencePolicy', flags))
        self.assertTrue(self.errors('StatusPersistencePolicy', 'checkpoint_for_transfer'))
        flags.pop('cleanup_on_death')
        self.assertTrue(self.errors('StatusPersistencePolicy', flags))

    def test_open_reviews_have_explicit_completion_criteria(self):
        registry = copy.deepcopy(self.registry)
        issue = next(issue for issue in registry['review_issues'] if issue['state'] == 'open')
        issue.pop('completion_criteria')
        self.assertTrue(any('actionable completion criteria' in error for error in model_errors(registry, ROOT)))

    def test_contract_and_content_versions_cannot_disagree(self):
        registry = copy.deepcopy(self.registry)
        registry['content_version'] = '2.0.0-design'
        self.assertTrue(any('content versions disagree' in error for error in validate_registry(registry)))


if __name__ == '__main__':
    unittest.main()
