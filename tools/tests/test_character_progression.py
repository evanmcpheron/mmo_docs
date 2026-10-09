"""Static source/fixture assertions, not Unreal gameplay or persistence tests."""
from __future__ import annotations

import bisect
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CREATION_FIELDS = [
    'RequestId', 'Name', 'AppearanceIds', 'FactionId',
    'CombatDisciplineId', 'VocationId',
]
VOCATION_FIELDS = {
    'TotalXP', 'DefinitionVersion', 'MasteryXP', 'UnspentMasteryPoints',
    'PurchasedSkillIds', 'PurchasedTalentIds', 'LearnedRecipeIds',
    'UnlockedTechniqueIds', 'AccomplishmentIds',
}


def incomplete_creation_signatures(text: str) -> list[str]:
    """Catch an obsolete signature anywhere a canonical source repeats it."""
    return [
        signature
        for signature in re.findall(r'CreateCharacter\(([^)]*)\)', text)
        if [field.strip() for field in signature.split(',')] != CREATION_FIELDS
    ]


class CharacterProgressionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = {
            name: json.loads((ROOT / f'sources/{name}.json').read_text(encoding='utf-8'))
            for name in [
                'manual-pages', 'current-asset-manifest', 'system-coverage',
                'phase-integration', 'design-decisions', 'profession-loops',
            ]
        }
        cls.pages = {page['path']: page for page in cls.sources['manual-pages']['pages']}
        cls.assets = {
            asset['name']: asset
            for asset in cls.sources['current-asset-manifest']['assets']
        }
        cls.fixture_sections = {
            section['title']: section
            for section in cls.pages['assets/Tests/Fixture_identity.html']['sections']
        }
        cls.fixture = json.loads(
            cls.fixture_sections['Machine-readable progression fixture']['code']
        )

    def page_text(self, path: str) -> str:
        return json.dumps(self.pages[path], ensure_ascii=False)

    def test_all_repeated_creation_signatures_require_three_identities(self) -> None:
        text = json.dumps(self.sources, ensure_ascii=False)
        self.assertGreaterEqual(text.count('CreateCharacter('), 17)
        self.assertEqual(incomplete_creation_signatures(text), [])
        self.assertEqual(self.fixture['required_creation_fields'], CREATION_FIELDS)

    def test_obsolete_creation_signatures_are_detected(self) -> None:
        for missing in ['FactionId', 'CombatDisciplineId', 'VocationId']:
            with self.subTest(missing=missing):
                signature = 'CreateCharacter(' + ', '.join(
                    field for field in CREATION_FIELDS if field != missing
                ) + ')'
                self.assertEqual(len(incomplete_creation_signatures(signature)), 1)
        signature = 'CreateCharacter(' + ', '.join(CREATION_FIELDS) + ')'
        self.assertEqual(incomplete_creation_signatures(signature), [])

    def test_independent_required_selection_validation_is_explicit(self) -> None:
        sections = self.pages['systems/identity.html']['sections']
        selection = next(
            section for section in sections
            if section['title'] == 'Required selections and permanent identity guards'
        )
        self.assertEqual(
            {row[0] for row in selection['table']['rows']},
            {'FactionId', 'CombatDisciplineId', 'VocationId'},
        )
        text = json.dumps(selection)
        for error in [
            'FactionRequired', 'FactionUnavailable', 'IdentityCatalogUnavailable',
            'CombatDisciplineRequired', 'CombatDisciplineUnavailable',
            'VocationRequired', 'VocationUnavailable', 'PermanentIdentityLocked',
            'RequestIdentityConflict',
        ]:
            self.assertIn(error, text)

    def test_discipline_ids_resolve_existing_definitions(self) -> None:
        identifiers = []
        for name in ['Vanguard', 'Ranger', 'Arcanist', 'Warden']:
            asset = self.assets[f'DA_Discipline_{name}']
            identifier = next(row[2] for row in asset['properties'] if row[0] == 'DefinitionId')
            self.assertIn('UCombatDisciplineDefinition', asset['dependencies'])
            identifiers.append(identifier)
        self.assertEqual(identifiers, self.fixture['combat_discipline_ids'])
        vocation_ids = {
            vocation['vocation_id']
            for vocation in self.sources['profession-loops']['vocational_contracts']
        }
        self.assertEqual(set(self.fixture['vocation_ids']), vocation_ids)
        pairs = {(discipline, vocation) for discipline in identifiers for vocation in vocation_ids}
        self.assertEqual(len(pairs), 20)
        self.assertIn('every available vocation', self.page_text('systems/identity.html'))

    def test_record_retains_one_active_selector_and_one_progression_owner(self) -> None:
        properties = {row[0]: row for row in self.assets['Record_Character']['properties']}
        for required in [
            'FactionId', 'CombatDisciplineId', 'VocationId', 'Progression',
            'Progression.Combat', 'Progression.Vocations',
            'Progression.Vocations[VocationId]', 'Revision / SchemaVersion',
        ]:
            self.assertIn(required, properties)
        for forbidden in ['ClassId', 'ActiveVocationId', 'CombatLevel', 'VocationLevel']:
            self.assertNotIn(forbidden, properties)
        self.assertEqual(self.fixture['active_vocation_field'], 'VocationId')
        self.assertEqual(self.fixture['permanent_fields'], ['FactionId', 'CombatDisciplineId'])
        self.assertEqual(self.fixture['combat_progression_path'], 'Progression.Combat')
        self.assertEqual(self.fixture['vocation_progression_path'], 'Progression.Vocations')
        self.assertIn('map<stable VocationId', properties['Progression.Vocations'][1])
        self.assertEqual(
            {field.strip() for field in properties['Progression.Vocations[VocationId]'][1].split(',')},
            VOCATION_FIELDS,
        )

    def test_all_retained_vocation_facts_have_fixture_values(self) -> None:
        self.assertEqual(set(self.fixture['vocation_value_fields']), VOCATION_FIELDS)
        for identifier, record in self.fixture['saved_vocations'].items():
            with self.subTest(vocation=identifier):
                self.assertIn(identifier, self.fixture['vocation_ids'])
                self.assertEqual(set(record), VOCATION_FIELDS)
                self.assertNotIn('VocationId', record)
                self.assertNotIn('Level', record)
                for field, value in record.items():
                    if isinstance(value, list):
                        self.assertEqual(len(value), len(set(value)))
                        self.assertTrue(value, f'{field} must exercise retention, not an empty case')
                    else:
                        self.assertIs(type(value), int)
                        self.assertGreaterEqual(value, 0)

    def test_return_sequence_restores_saved_xp_and_derived_levels(self) -> None:
        thresholds = self.fixture['test_level_thresholds']
        self.assertEqual(thresholds[0], 0)
        self.assertTrue(all(left < right for left, right in zip(thresholds, thresholds[1:])))
        sequence = self.fixture['sequence']
        self.assertEqual([step['expected_level'] for step in sequence], [20, 1, 12, 20, 12])
        previously_retained = set()
        for step in sequence:
            with self.subTest(step=step['step']):
                self.assertEqual(bisect.bisect_right(thresholds, step['expected_xp']), step['expected_level'])
                retained = set(step['retained'])
                self.assertIn(step['active'], retained)
                self.assertTrue(previously_retained <= retained)
                previously_retained = retained
                self.assertTrue(step['combat_unchanged'])
                self.assertEqual(step['replayed_rewards'], 0)
                if step['step'].startswith('return_'):
                    self.assertEqual(
                        step['expected_xp'],
                        self.fixture['saved_vocations'][step['active']]['TotalXP'],
                    )
        self.assertEqual(
            bisect.bisect_right(thresholds, self.fixture['combat_snapshot']['TotalXP']), 35
        )
        self.assertEqual(self.fixture['independent_level_pairs'], [[40, 5], [10, 30]])

    def test_definition_initial_xp_and_versioned_curves_are_explicit(self) -> None:
        properties = {row[0]: row for row in self.assets['UVocationDefinition']['properties']}
        self.assertIn('Level 1', properties['InitialXP'][2])
        self.assertIn('DefinitionVersion', properties['ContentVersion'][2])
        self.assertIn('no combat-level input', properties['LevelThresholds'][2])
        combat_properties = {row[0] for row in self.assets['UCombatDisciplineDefinition']['properties']}
        self.assertIn('LevelThresholds', combat_properties)
        self.assertIn('ContentVersion', combat_properties)

    def test_trainer_policy_is_not_rebalanced(self) -> None:
        policy = next(
            section for section in self.pages['design/vocational-identity.html']['sections']
            if section['title'] == 'Recommended initial change policy'
        )
        rows = dict(policy['table']['rows'])
        self.assertEqual(rows['When may a character change?'], 'After the introduction and three varied vocation contracts. This is an activity commitment, not a real-time daily/login gate.')
        self.assertEqual(rows['Where?'], 'An appropriate trainer; the server validates range, eligibility and pending transactions.')
        self.assertEqual(rows['Cost?'], 'An explicit affordable retraining contract and a published currency fee; exact fee is a tuning decision still to author. No punitive item wipe.')
        self.assertEqual(rows['Cooldown?'], 'Complete three varied contracts in the new vocation before another switch. No mandatory calendar wait.')

    def test_switch_uses_existing_transaction_and_receipt_framework(self) -> None:
        page = self.pages['design/vocational-identity.html']
        contract = next(
            section for section in page['sections']
            if section['title'] == 'Server-authoritative ChangeVocation contract'
        )
        self.assertEqual(len(contract['steps']), 7)
        text = json.dumps(contract)
        for required in [
            'UDurableStateClient', 'LeaseEpoch', 'ExpectedRevisions', 'ContentVersion',
            'TargetVocationId', 'TrainerId', 'Record_CommandReceipt', 'outbox',
            'IncompatiblePendingOperation', 'AlreadyActive', 'RequestIdentityConflict',
            'Progression.Combat', 'Progression.Vocations', 'byte-for-byte',
        ]:
            self.assertIn(required, text)
        self.assertIn('before current trainer/eligibility/revision checks', contract['steps'][0])
        self.assertIn('runtime handles are not stored', self.page_text('design/vocational-identity.html'))

    def test_permissions_awards_and_recovery_are_not_ui_owned(self) -> None:
        text = self.page_text('design/vocational-identity.html')
        for invariant in [
            'authoritative ability activation and crafting acceptance/commit',
            'preserve class/equipment/general-activity grants',
            'CombatXP and targeted VocationXP',
            'StaleRevision', 'old epoch', 'original receipt without changing current state',
            'Pawn, UI, Data Asset or a second progression owner',
        ]:
            self.assertIn(invariant, text)
        self.assertIn('same unique quest outcome/receipt', json.dumps(self.sources['system-coverage']))

    def test_migration_preserves_history_and_requires_unresolved_identity_decisions(self) -> None:
        text = self.page_text('assets/Persistence/Record_Character.html')
        for safeguard in [
            'MigrationNeedsIdentitySelection', 'one-time legacy completion',
            'Reapplying the migration to schema 2 is a no-op',
            'deprecated fields remain read-only', 'missing active key',
            'unsupported schema/definition version', 'quarantine',
            'never dual-written', 'without replaying threshold rewards',
            'never its position, display name',
        ]:
            self.assertIn(safeguard, text)

    def test_every_required_future_game_scenario_is_documented(self) -> None:
        matrix = self.fixture_sections['Future-game progression acceptance matrix']
        rows = matrix['table']['rows']
        self.assertEqual({row[0] for row in rows}, {
            'create_valid', 'missing_class', 'missing_vocation', 'unavailable_selection',
            'permanent_identity', 'first_training', 'restore_history', 'repeat_switch',
            'combat_unchanged', 'inactive_permission', 'lifecycle', 'receipt_replay',
            'concurrent_changes', 'pending_and_faults', 'independent_awards',
            'migration', 'solo_and_clients',
        })
        self.assertEqual(len(rows), 17)
        self.assertTrue(all(len(row) == 3 and all(row) for row in rows))
        self.assertIn('NOT RUN IN UNREAL', ' '.join(matrix['paragraphs']))
        self.assertEqual(self.fixture['status'], 'not_run_in_unreal')
        self.assertEqual(self.fixture['populations'], [1, 2, 5, 10, 30])

    def test_phase_integration_preserves_creation_order_and_readiness_gates(self) -> None:
        phases = self.sources['phase-integration']['phases']
        self.assertEqual([phase['phase'] for phase in phases], list(range(32)))
        self.assertIn('UCombatDisciplineDefinition', phases[12]['creates'])
        self.assertNotIn('UCombatDisciplineDefinition', phases[5]['creates'])
        self.assertIn('approved faction', phases[5]['editor_steps'])
        self.assertIn('Progression.Vocations', phases[6]['native_contract'])
        self.assertIn('permanently selected', phases[12]['native_contract'])
        self.assertIn('ChangeVocation', phases[13]['native_contract'])
        for number in [5, 6, 12, 13]:
            self.assertEqual(phases[number]['runtime_test'], 'not_run')

    def test_confirmed_decision_does_not_mark_runtime_implemented(self) -> None:
        decisions = self.sources['design-decisions']['decisions']
        decision = next(value for value in decisions if value['id'] == 'ADR-006')['decision']
        self.assertIn('Committed requirement', decision)
        self.assertIn('unresolved integration dependency', decision)
        for name in ['Record_Character', 'UVocationDefinition', 'UCombatDisciplineDefinition']:
            self.assertEqual(self.assets[name]['documentation_status'], 'initial_contract')
            self.assertEqual(self.assets[name]['verification']['runtime'], 'not_run')


if __name__ == '__main__':
    unittest.main()
