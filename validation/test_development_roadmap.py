"""Regression tests for roadmap graph, completion evidence and derived progress."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_development_roadmap import load, milestone_progress, prerequisite_closure, progress, ready_epics
from check_development_roadmap import roadmap_errors


class RoadmapTests(unittest.TestCase):
    def setUp(self):
        self.data = deepcopy(load())
        self.by_id = {e['id']: e for e in self.data['epics']}

    def errors(self, generated=False):
        return roadmap_errors(self.data, check_generated=generated)

    def complete(self, identifier):
        epic = self.by_id[identifier]
        epic['status'] = 'Complete'
        epic['verified_evidence'] = [{
            'criteria': list(range(1, len(epic['acceptance_criteria']) + 1)),
            'artifact': 'https://example.com/test-only-evidence', 'revision': 'test-fixture-revision',
            'result': 'Passed', 'summary': 'Synthetic validator fixture; never written to the roadmap.',
        }]

    def test_published_registry_and_static_page_are_current(self):
        self.assertEqual([], self.errors(generated=True))

    def test_unknown_dependency_is_rejected(self):
        self.data['epics'][0]['hard_dependencies'].append('BW-999999')
        self.assertTrue(any('undefined epic' in e for e in self.errors()))

    def test_dependency_cycle_is_rejected(self):
        self.by_id['BW-001']['hard_dependencies'] = ['BW-002']
        self.by_id['BW-002']['hard_dependencies'] = ['BW-001']
        self.assertTrue(any('Hard dependency cycle' in e for e in self.errors()))

    def test_duplicate_ids_are_rejected(self):
        self.data['epics'][1]['id'] = self.data['epics'][0]['id']
        self.assertTrue(any('Duplicate stable IDs' in e for e in self.errors()))

    def test_recommended_predecessor_is_not_a_hard_gate(self):
        epic = self.by_id['BW-018']
        for dependency in prerequisite_closure(self.data, epic['hard_dependencies']):
            self.complete(dependency)
        ready = {e['id'] for e in ready_epics(self.data)}
        self.assertIn('BW-018', ready)
        self.assertEqual('Not Started', self.by_id['BW-003']['status'])
        self.assertEqual([], self.errors())

    def test_status_and_blocker_rules(self):
        self.data['epics'][0]['status'] = 'Done'
        self.assertTrue(any('invalid status' in e for e in self.errors()))
        self.data['epics'][0]['status'] = 'Blocked'
        self.assertTrue(any('Blocked requires' in e for e in self.errors()))
        self.data['epics'][0]['blockers'] = ['An explicit external constraint.']
        self.assertEqual([], self.errors())
        self.assertNotIn(self.data['epics'][0], ready_epics(self.data))

    def test_complete_requires_passing_evidence_for_every_ac(self):
        epic = self.data['epics'][0]
        epic['status'] = 'Complete'
        self.assertTrue(any('passing evidence for every AC' in e for e in self.errors()))
        self.complete(epic['id'])
        epic['verified_evidence'][0]['criteria'].pop()
        self.assertTrue(any('passing evidence for every AC' in e for e in self.errors()))
        self.complete(epic['id'])
        epic['verified_evidence'][0]['result'] = 'Failed'
        self.assertTrue(any('failing current evidence' in e for e in self.errors()))

    def test_complete_requires_current_prerequisites(self):
        self.complete('BW-018')
        self.assertTrue(any('complete hard prerequisites' in e for e in self.errors()))

    def test_progress_changes_all_derived_views_without_duplicate_status(self):
        for epic in self.data['epics']:
            epic['status'] = 'Not Started'
            epic['verified_evidence'] = []
            epic['blockers'] = []
        self.complete('BW-001')
        self.assertEqual([], self.errors())
        overall = progress(self.data['epics'])
        self.assertEqual(1, overall['complete'])
        self.assertEqual(round(100 / len(self.data['epics']), 1), overall['percentage'])
        phase = [e for e in self.data['epics'] if e['phase'] == self.by_id['BW-001']['phase']]
        self.assertEqual('In Progress', progress(phase)['status'])
        self.assertEqual('In Progress', milestone_progress(self.data, self.data['milestones'][0])['status'])
        self.assertTrue(any('Stale generated roadmap' in e for e in self.errors(generated=True)))

    def test_component_completion_does_not_complete_integration_milestone(self):
        milestone = self.data['milestones'][1]
        for identifier in prerequisite_closure(self.data, milestone['required_epics']):
            if identifier not in ('BW-012', 'BW-083'):
                self.complete(identifier)
        self.assertNotEqual('Complete', milestone_progress(self.data, milestone)['status'])
        self.assertEqual('Not Started', self.by_id['BW-012']['status'])

    def test_final_milestone_cannot_omit_a_branch(self):
        self.data['milestones'][-1]['required_epics'] = ['BW-092']
        self.assertTrue(any('Final full-game milestone' in e for e in self.errors()))

    def test_technical_proof_does_not_require_economic_characters(self):
        closure = prerequisite_closure(self.data, ['BW-012'])
        self.assertNotIn('BW-018', closure)
        self.assertNotIn('BW-019', closure)

    def test_external_persistent_play_requires_security_restore_and_prediction(self):
        opening = next(m for m in self.data['milestones'] if m['id'] == 'milestone-opening')
        closure = prerequisite_closure(self.data, opening['required_epics'])
        self.assertTrue({'BW-008', 'BW-086', 'BW-087'} <= set(closure))

    def test_item_use_and_conversion_do_not_require_personal_crafting(self):
        for identifier in ('BW-075', 'BW-076'):
            self.assertNotIn('BW-037', prerequisite_closure(self.data, [identifier]))

    def test_production_gate_reaches_every_epic_including_pve_level_sync(self):
        closure = set(prerequisite_closure(self.data, ['BW-094']))
        self.assertEqual(set(self.by_id), closure)
        self.assertIn('BW-077', closure)

    def test_feature_traceability_cannot_silently_disappear(self):
        for row in self.data['coverage'] + self.data['epics']:
            row['related_docs'] = [d for d in row['related_docs'] if d['href'] != 'professions/blacksmithing.html']
        self.assertTrue(any('Feature pages without roadmap traceability' in e for e in self.errors()))

    def test_planning_ids_allow_gaps_without_numeric_priority(self):
        original, replacement = 'BW-001', 'BW-200'
        self.by_id[original]['id'] = replacement
        for row in self.data['epics']:
            for field in ('hard_dependencies', 'recommended_predecessors'):
                row[field] = [replacement if i == original else i for i in row[field]]
        for row in self.data['milestones']:
            row['required_epics'] = [replacement if i == original else i for i in row['required_epics']]
        for row in self.data['coverage'] + self.data['sequencing_decisions'] + self.data['open_decisions']:
            row['epics'] = [replacement if i == original else i for i in row['epics']]
        self.assertEqual([], self.errors())


if __name__ == '__main__':
    unittest.main()
