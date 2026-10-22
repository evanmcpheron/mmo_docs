"""Regression tests for roadmap graph, completion evidence and derived progress."""
from copy import deepcopy
from html import escape
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_development_roadmap import (PAGE, address, anchor_page, epic_page, generated_page_paths,
                                      generated_pages, load, milestone_progress, phase_page,
                                      prerequisite_closure, progress, ready_epics, ticket_page)
from check_development_roadmap import Anchors, roadmap_errors


class RoadmapTests(unittest.TestCase):
    def setUp(self):
        self.data = deepcopy(load())
        self.by_id = {e['id']: e for e in self.data['epics']}

    def errors(self, generated=False):
        return roadmap_errors(self.data, check_generated=generated)

    def reset_epic_and_ticket_progress(self, identifier):
        records = [self.by_id[identifier]] + [ticket for ticket in self.data['tickets']
                                             if ticket['parent_epic'] == identifier]
        for record in records:
            record['status'] = 'Not Started'
            record['verified_evidence'] = []
            record['blockers'] = []

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

    def test_dashboard_and_phases_are_indexes_and_each_epic_has_its_own_page(self):
        outputs = generated_pages(self.data)
        self.assertEqual(set(generated_page_paths(self.data)), set(outputs))
        self.assertEqual([], Anchors(outputs[PAGE]).epic_ids)
        for phase in self.data['phases']:
            expected = [e['id'] for e in self.data['epics'] if e['phase'] == phase['id']]
            source = outputs[phase_page(phase)]
            parsed = Anchors(source)
            self.assertEqual([], parsed.epic_ids)
            for identifier in expected:
                page = epic_page(self.data, identifier)
                self.assertEqual(address(page, phase_page(phase), identifier), parsed.link_targets[identifier])
                self.assertEqual([identifier], Anchors(outputs[page]).epic_ids)
                for criterion in self.by_id[identifier]['acceptance_criteria']:
                    self.assertIn(escape(criterion), ' '.join(outputs[page].split()))

    def test_acceptance_criteria_have_direct_links_for_future_tickets(self):
        outputs = generated_pages(self.data)
        for epic in self.data['epics']:
            source = outputs[epic_page(self.data, epic['id'])]
            parsed = Anchors(source)
            for number, criterion in enumerate(epic['acceptance_criteria'], 1):
                anchor = f'{epic["id"]}-AC-{number}'
                self.assertIn(anchor, parsed.ids)
                self.assertIn('#' + anchor, parsed.references)
                self.assertIn(escape(criterion), ' '.join(source.split()))

    def test_dependencies_and_dependents_link_in_both_directions(self):
        outputs = generated_pages(self.data)
        for epic in self.data['epics']:
            page = epic_page(self.data, epic['id'])
            for dependency in epic['hard_dependencies']:
                other = epic_page(self.data, dependency)
                self.assertIn(address(other, page, dependency), Anchors(outputs[page]).references)
                self.assertIn(address(page, other, epic['id']), Anchors(outputs[other]).references)

    def test_tickets_link_to_parent_criteria_and_dependencies_and_are_searchable(self):
        from build_data_inventory import roadmap_search
        outputs = generated_pages(self.data)
        search = {r['url'] for r in roadmap_search()}
        for ticket in self.data['tickets']:
            page = ticket_page(ticket['id'])
            parent = epic_page(self.data, ticket['parent_epic'])
            parsed = Anchors(outputs[page])
            self.assertIn(ticket['id'], parsed.ids)
            self.assertIn(address(parent, page, ticket['parent_epic']), parsed.references)
            self.assertIn(address(page, parent, ticket['id']), Anchors(outputs[parent]).references)
            self.assertIn(page + '#' + ticket['id'], search)
            for anchor in ticket['epic_criteria']:
                self.assertIn(address(parent, page, anchor), parsed.references)
            for dependency in ticket['dependencies']:
                self.assertIn(address(anchor_page(self.data, dependency), page, dependency), parsed.references)

    def test_ticket_coverage_rejects_missing_and_foreign_epic_criteria(self):
        for ticket in self.data['tickets']:
            ticket['epic_criteria'] = [c for c in ticket['epic_criteria'] if c != 'BW-003-AC-4'] or ['BW-003-AC-1']
        self.assertTrue(any('tickets must cover every epic' in e for e in self.errors()))
        self.data['tickets'][0]['epic_criteria'] = ['BW-002-AC-1']
        self.assertTrue(any('exact parent AC anchors' in e for e in self.errors()))

    def test_ticket_dependency_order_rejects_cycles_and_unknown_dependencies(self):
        self.data['tickets'][0]['dependencies'] = ['BW-003-T05']
        self.assertTrue(any('conflicts with execution order' in e for e in self.errors()))
        self.data['tickets'][0]['dependencies'] = ['BW-003-T99']
        self.assertTrue(any('undefined dependency' in e for e in self.errors()))
        self.data['tickets'][0]['dependencies'] = ['BW-003']
        self.assertTrue(any('own parent epic' in e for e in self.errors()))

    def test_ticket_manual_test_requires_runnable_steps_or_explicit_rationale(self):
        test = self.data['tickets'][0]['manual_test']
        del test['reset']
        self.assertTrue(any('manual test needs' in e for e in self.errors()))
        self.data['tickets'][0]['manual_test'] = {'not_applicable': 'Synthetic documentation-only validator fixture.'}
        self.assertEqual([], self.errors())

    def test_ticket_completion_requires_executed_evidence_and_dependencies(self):
        for existing in self.data['tickets']:
            existing['status'] = 'Not Started'
            existing['verified_evidence'] = []
            existing['blockers'] = []
        ticket = self.data['tickets'][1]
        ticket['status'] = 'Complete'
        ticket['blockers'] = []
        ticket['verified_evidence'] = []
        self.assertTrue(any('Complete requires passing evidence' in e for e in self.errors()))
        ticket['verified_evidence'] = [{
            'criteria': list(range(1, len(ticket['acceptance_criteria']) + 1)),
            'artifact': 'https://example.com/test-only-ticket-evidence', 'revision': 'synthetic-fixture',
            'result': 'Passed', 'summary': 'Synthetic executed evidence fixture; never written to registry.',
        }]
        self.assertTrue(any('Complete requires complete dependencies' in e for e in self.errors()))
        ticket['dependencies'] = []
        self.assertEqual([], self.errors())
        ticket['blockers'] = ['Synthetic unfinished verification.']
        self.assertTrue(any('no blockers or failures' in e for e in self.errors()))
        ticket['blockers'] = []
        ticket['verified_evidence'][0]['result'] = 'Not Executed'
        self.assertTrue(any('evidence result must be Passed or Failed' in e for e in self.errors()))

    def test_malformed_ticket_text_lists_are_reported_without_crashing(self):
        ticket = self.data['tickets'][0]
        ticket['status'] = 'Complete'
        for field in ('scope', 'out_of_scope', 'epic_criteria', 'acceptance_criteria'):
            original = ticket[field]
            for value in (None, 'invalid', [], [None]):
                with self.subTest(field=field, value=value):
                    ticket[field] = value
                    self.assertTrue(any(field + ' requires nonempty text entries' in e for e in self.errors()))
            ticket[field] = original

    def test_ticket_planning_does_not_promote_epic_or_readiness(self):
        for epic in self.data['epics']:
            self.reset_epic_and_ticket_progress(epic['id'])
        self.complete('BW-001')
        self.by_id['BW-002']['status'] = 'In Progress'
        before = progress(self.data['epics'])
        ready = [e['id'] for e in ready_epics(self.data)]
        self.data['tickets'][0]['status'] = 'In Progress'
        self.assertEqual(before, progress(self.data['epics']))
        self.assertEqual(ready, [e['id'] for e in ready_epics(self.data)])
        self.assertEqual('Not Started', self.by_id['BW-003']['status'])
        self.assertNotIn('BW-003', ready)
        self.assertEqual([], self.errors())

    def test_epic_previous_and_next_follow_the_recommended_sequence(self):
        outputs = generated_pages(self.data)
        for index, epic in enumerate(self.data['epics']):
            page = epic_page(self.data, epic['id'])
            source = outputs[page]
            for offset, relation in ((-1, 'prev'), (1, 'next')):
                target = index + offset
                if 0 <= target < len(self.data['epics']):
                    other = self.data['epics'][target]
                    href = address(epic_page(self.data, other['id']), page, other['id'])
                    self.assertIn(f'href="{href}" rel="{relation}"', ' '.join(source.split()))
                else:
                    self.assertNotIn(f'rel="{relation}"', source)

    def test_legacy_bookmarks_offer_direct_canonical_shortcuts_without_javascript(self):
        dashboard = Anchors(generated_pages(self.data)[PAGE])
        for row in self.data['epics'] + self.data['milestones'] + self.data['sequencing_decisions'] + self.data['open_decisions']:
            identifier = row['id']
            self.assertEqual(address(anchor_page(self.data, identifier), PAGE, identifier), dashboard.link_targets[identifier])

    def test_cross_phase_prerequisites_open_their_defining_phase(self):
        outputs = generated_pages(self.data)
        dependent = 'BW-019'
        prerequisite = 'BW-004'
        page = epic_page(self.data, dependent)
        self.assertNotEqual(page, epic_page(self.data, prerequisite))
        self.assertIn(address(epic_page(self.data, prerequisite), page, prerequisite), Anchors(outputs[page]).references)

    def test_a_stale_phase_is_detected_even_when_the_dashboard_is_unchanged(self):
        from unittest.mock import patch
        original_read = Path.read_text
        target = ROOT / phase_page(self.data['phases'][0])

        def read(path, *args, **kwargs):
            source = original_read(path, *args, **kwargs)
            return source + '\n' if path == target else source

        with patch.object(Path, 'read_text', read):
            self.assertTrue(any('Stale generated roadmap: ' + target.relative_to(ROOT).as_posix() in error
                                for error in self.errors(generated=True)))

    def test_a_stale_epic_is_detected_even_when_its_phase_is_unchanged(self):
        from unittest.mock import patch
        original_read = Path.read_text
        target = ROOT / epic_page(self.data, 'BW-097')

        def read(path, *args, **kwargs):
            source = original_read(path, *args, **kwargs)
            return source + '\n' if path == target else source

        with patch.object(Path, 'read_text', read):
            self.assertTrue(any('Stale generated roadmap: ' + target.relative_to(ROOT).as_posix() in error
                                for error in self.errors(generated=True)))

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
        for existing in self.data['epics']:
            self.reset_epic_and_ticket_progress(existing['id'])
        epic = self.by_id['BW-018']
        for dependency in prerequisite_closure(self.data, epic['hard_dependencies']):
            self.complete(dependency)
        ready = {e['id'] for e in ready_epics(self.data)}
        self.assertIn('BW-018', ready)
        self.assertEqual('Not Started', self.by_id['BW-003']['status'])
        self.assertEqual([], self.errors())

    def test_status_and_blocker_rules(self):
        epic = self.by_id['BW-099']
        epic['status'] = 'Done'
        self.assertTrue(any('invalid status' in e for e in self.errors()))
        epic['status'] = 'Blocked'
        self.assertTrue(any('Blocked requires' in e for e in self.errors()))
        epic['blockers'] = ['An explicit external constraint.']
        self.assertEqual([], self.errors())
        self.assertNotIn(epic, ready_epics(self.data))

    def test_complete_requires_passing_evidence_for_every_ac(self):
        epic = self.data['epics'][0]
        epic['status'] = 'Complete'
        epic['verified_evidence'] = []
        self.assertTrue(any('passing evidence for every AC' in e for e in self.errors()))
        self.complete(epic['id'])
        epic['verified_evidence'][0]['criteria'].pop()
        self.assertTrue(any('passing evidence for every AC' in e for e in self.errors()))
        self.complete(epic['id'])
        epic['verified_evidence'][0]['result'] = 'Failed'
        self.assertTrue(any('failing current evidence' in e for e in self.errors()))

    def test_complete_requires_current_prerequisites(self):
        prerequisite = self.by_id['BW-018']['hard_dependencies'][0]
        self.by_id[prerequisite]['status'] = 'In Progress'
        self.complete('BW-018')
        self.assertTrue(any('complete hard prerequisites' in e for e in self.errors()))
        self.complete(prerequisite)
        self.assertEqual([], self.errors())

    def test_progress_changes_all_derived_views_without_duplicate_status(self):
        for epic in self.data['epics']:
            self.reset_epic_and_ticket_progress(epic['id'])
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
        renamed_tickets = {ticket['id']: ticket['id'].replace(original, replacement, 1)
                           for ticket in self.data['tickets'] if ticket['parent_epic'] == original}
        for ticket in self.data['tickets']:
            if ticket['parent_epic'] == original:
                ticket['parent_epic'] = replacement
                ticket['id'] = renamed_tickets[ticket['id']]
                ticket['epic_criteria'] = [anchor.replace(original, replacement, 1)
                                           for anchor in ticket['epic_criteria']]
            ticket['dependencies'] = [renamed_tickets.get(i, replacement if i == original else i)
                                      for i in ticket['dependencies']]
        self.assertEqual([], self.errors())


if __name__ == '__main__':
    unittest.main()
