"""Prevent original-game setup from becoming a project port or module recreation."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import check_phase_integration
from build_manual_indexes import asset_identity, prepare_page
from validate_documentation import registry_errors


class ProjectBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets = json.loads((ROOT / 'sources/current-asset-manifest.json').read_text())['assets']
        cls.by_name = {asset['name']: asset for asset in cls.assets}
        cls.phases = json.loads((ROOT / 'sources/phase-integration.json').read_text())['phases']
        cls.pages = json.loads((ROOT / 'sources/manual-pages.json').read_text())['pages']
        cls.by_path = {page['path']: page for page in cls.pages}

    def check_changed_phase(self, field, value):
        phases = copy.deepcopy(self.phases)
        phases[0][field] = value
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'sources').mkdir()
            records = {
                'phase-integration.json': {'phases': phases},
                'current-asset-manifest.json': {'assets': self.assets},
                'manual-pages.json': {'pages': self.pages},
            }
            for filename, record in records.items():
                (root / 'sources' / filename).write_text(json.dumps(record))
            with patch.object(check_phase_integration, 'ROOT', root):
                return check_phase_integration.check()['errors']

    def test_original_game_premise_at_entry_points(self):
        for path in ['index.html', 'getting-started.html', 'architecture.html', 'game-overview.html', 'development-roadmap.html']:
            with self.subTest(path=path):
                text = ' '.join(self.by_path[path]['sections'][0]['paragraphs'])
                self.assertIn('original 2D pixel-art fantasy MMORPG', text)
                self.assertIn('existing Briarwake Unreal repository', text)
                self.assertIn('No previous game implementation, port or conversion is required', text)

    def test_module_is_existing_with_stable_documentation_identity(self):
        module = self.by_name['Briarwake']
        self.assertEqual(module['native_module'], 'RPG')
        self.assertEqual(module['exact_game_path_or_source_path'], 'Source/RPG/RPG.Build.cs')
        self.assertEqual(module['doc_path'], 'assets/Core/Briarwake.html')
        self.assertEqual(module['creation_mode'], 'verify_existing')
        self.assertEqual(module['status'], 'source-inspected')
        self.assertEqual(module['verification']['engine_compile'], 'not_run')
        self.assertEqual(module['verification']['runtime'], 'not_run')
        self.assertTrue((ROOT / module['source_evidence']).is_file())

    def test_all_planned_native_paths_use_existing_module(self):
        for asset in self.assets:
            path = asset['exact_game_path_or_source_path']
            if path.startswith('Source/'):
                self.assertTrue(path.startswith('Source/RPG/'), (asset['name'], path))

    def test_phase_zero_only_verifies_module(self):
        self.assertEqual(self.phases[0]['creates'], [])
        self.assertEqual(self.phases[0]['activates'], [])
        self.assertEqual(self.phases[0]['verifies_existing'], ['Briarwake'])
        preparation = json.loads((ROOT / 'sources/phase-creation-order.json').read_text())
        self.assertEqual(preparation['verifies_existing'], ['Briarwake'])
        self.assertEqual(preparation['order'][0], 'Briarwake')
        self.assertEqual(check_phase_integration.check()['errors'], [])

    def test_recreating_existing_module_is_rejected(self):
        self.assertTrue(any('incorrect creation set' in error for error in self.check_changed_phase('creates', ['Briarwake'])))

    def test_reactivating_existing_module_is_rejected(self):
        self.assertTrue(any('incorrect activation set' in error for error in self.check_changed_phase('activates', ['Briarwake'])))

    def test_missing_or_duplicate_verification_is_rejected(self):
        self.assertTrue(any('verification set' in error for error in self.check_changed_phase('verifies_existing', [])))
        self.assertTrue(any('duplicate verifies_existing' in error for error in self.check_changed_phase('verifies_existing', ['Briarwake', 'Briarwake'])))

    def test_existing_status_without_source_evidence_is_rejected(self):
        changed = copy.deepcopy(self.assets)
        del changed[0]['source_evidence']
        self.assertTrue(any('requires source-inspected evidence' in error for error in registry_errors(changed)))
        changed = copy.deepcopy(self.assets)
        changed[0]['creation_mode'] = 'create'
        self.assertTrue(any('must be an existing prerequisite' in error for error in registry_errors(changed)))

    def test_generated_labels_do_not_instruct_module_creation(self):
        identity = dict(asset_identity(self.by_name['Briarwake'])['rows'])
        self.assertEqual(identity['Existing physical path'], 'Source/RPG/RPG.Build.cs')
        self.assertIn('Verify existing', identity)
        self.assertNotIn('Create / activate', identity)
        page = prepare_page(self.by_path['phases/phase-00.html'], self.by_name, self.phases)
        self.assertEqual(page['sections'][2]['table']['rows'][0][3], 'Verify existing; do not create')

    def test_history_url_and_superseded_decision_are_retained(self):
        page = self.by_path['architecture/source-migration.html']
        self.assertEqual(page['title'], 'Historical Documentation Reference and Design Differences')
        decisions = json.loads((ROOT / 'sources/design-decisions.json').read_text())['decisions']
        self.assertEqual(decisions[0]['historical_decision'], 'Briarwake name and Source/Briarwake paths supersede tentative RPG naming.')
        self.assertTrue(any(decision['id'] == 'ADR-011' for decision in decisions))

    def test_phases_remain_complete_and_migrations_remain_explicit(self):
        self.assertEqual([phase['phase'] for phase in self.phases], list(range(32)))
        for number in range(32):
            self.assertIn(f'phases/phase-{number:02d}.html', self.by_path)
        self.assertIn('Schema upgrades here concern versioned Briarwake records', self.phases[6]['native_contract'])
        self.assertIn('migration', self.phases[7]['build_target'])
        self.assertIn('migrations', self.phases[31]['build_target'])

    def test_later_targets_are_proposals_not_project_renames(self):
        self.assertIn('Only RPG and RPGEditor targets were observed', self.phases[4]['native_contract'])
        self.assertIn('proposed Phase 04 targets', self.phases[4]['run_now'])
        self.assertNotIn('BriarwakeServer', self.phases[4]['run_now'])
        self.assertNotIn('BriarwakeClient', self.phases[4]['run_now'])


if __name__ == '__main__':
    unittest.main()
