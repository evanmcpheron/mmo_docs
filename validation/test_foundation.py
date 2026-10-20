"""Regression coverage for native dependency gates, preservation and current-source search."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_data_inventory import SearchSections, feature_search, load_registry
from build_development_roadmap import load
from check_foundation import baseline_errors, foundation_errors


class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.roadmap = deepcopy(load())
        self.inventory = deepcopy(load_registry())
        for record in self.roadmap['epics'] + self.roadmap['tickets']:
            record.update(status='Not Started', blockers=[], verified_evidence=[])

    def test_network_gate_requires_supplied_plugin_verification(self):
        self.assertEqual([], foundation_errors(roadmap=self.roadmap))
        for epic in self.roadmap['epics']:
            if epic['id'] == 'BW-005':
                epic['hard_dependencies'].remove('BW-100')
        self.assertTrue(any('BW-005' in error for error in foundation_errors(roadmap=self.roadmap)))

    def test_zero_snapshot_rejects_progress_and_carried_evidence(self):
        self.assertEqual([], baseline_errors(roadmap=self.roadmap, inventory=self.inventory))
        self.roadmap['epics'][0]['status'] = 'Complete'
        self.roadmap['tickets'][0]['verified_evidence'] = [{'summary': 'Synthetic old result'}]
        errors = baseline_errors(roadmap=self.roadmap, inventory=self.inventory)
        self.assertTrue(any('BW-001:' in error for error in errors))
        self.assertTrue(any('BW-001-T01:' in error for error in errors))
        self.assertTrue(any('milestone' in error for error in errors))

    def test_preservation_rejects_contract_or_relationship_drift(self):
        self.inventory['entries'][0]['definition']['description'] = 'Synthetic incompatible meaning'
        errors = baseline_errors(roadmap=self.roadmap, inventory=self.inventory)
        self.assertIn('Canonical contract or relationship changed from the reviewed baseline', errors)

    def test_search_uses_current_main_sections_and_excludes_navigation_and_footer(self):
        source = ('<nav>old navigation</nav><main><h1>Current title</h1><p>Current body</p>'
                  '<h2 id="rule">Current rule</h2><p>Updated <code>value</code></p>'
                  '<footer>old footer</footer></main>')
        sections = SearchSections(source).sections
        self.assertEqual(['Current title', 'Current rule'], [s['title'] for s in sections])
        self.assertEqual('rule', sections[1]['anchor'])
        self.assertEqual('Updated value', ''.join(sections[1]['text']))
        self.assertNotIn('old', json.dumps(sections))

    def test_feature_index_contains_foundation_and_excludes_retained_runtime_pages(self):
        records = feature_search(self.inventory)
        self.assertTrue(any(record['url'] == 'guide/unreal-cpp.html#setup' for record in records))
        self.assertFalse(any(record['url'].startswith(('validation/', 'guide/roadmap-')) for record in records))

    def test_search_preserves_direct_current_content_entry_links(self):
        source = ('<main><h1>Abilities</h1><table><tr id="ability.example">'
                  '<td><strong>Example</strong></td><td>Updated effect</td></tr></table></main>')
        entry = next(s for s in SearchSections(source).sections if s['anchor'] == 'ability.example')
        self.assertEqual('Example', entry['title'])
        self.assertIn('Updated effect', ''.join(entry['text']))
        records = feature_search(self.inventory)
        self.assertTrue(any(r['url'] == 'classes/warrior.html#ability.warrior.iron_cut' for r in records))


if __name__ == '__main__':
    unittest.main()
