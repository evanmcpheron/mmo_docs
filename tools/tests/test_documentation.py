"""Positive and negative checks for documentation tooling, not game code."""
import copy
import json
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_manual_indexes import inline, relative_link, heading_id
from validate_documentation import PageParser, registry_errors, validate
from simulate_population_scaling import targets
from check_feature_coverage import check
ROOT = Path(__file__).resolve().parents[2]

class DocumentationTests(unittest.TestCase):

    def setUp(self):
        self.assets = json.loads((ROOT / 'sources/current-asset-manifest.json').read_text(encoding='utf-8'))['assets']

    def test_nested_relative_link(self):
        self.assertEqual(relative_link('assets/Items/Test.html', 'systems/items.html'), '../../systems/items.html')

    def test_text_and_link_are_escaped(self):
        self.assertEqual(inline('<script>x</script> `a<b`', 'index.html', {}), '&lt;script&gt;x&lt;/script&gt; <code>a&lt;b</code>')
        self.assertIn('A &amp; B', inline('[[glossary.html|A & B]]', 'index.html', {}))

    def test_unknown_asset_rejected(self):
        with self.assertRaises(ValueError):
            inline('[[asset:Unknown]]', 'index.html', {})

    def test_heading_ids_disambiguated(self):
        self.assertNotEqual(heading_id('Same heading', 1), heading_id('Same heading', 2))

    def test_registry_baseline(self):
        self.assertEqual(registry_errors(self.assets), [])

    def test_duplicate_identity_rejected(self):
        changed = copy.deepcopy(self.assets)
        changed.append(copy.deepcopy(changed[0]))
        self.assertTrue(any(('Duplicate name' in error for error in registry_errors(changed))))

    def test_reverse_dependency_rejected(self):
        changed = copy.deepcopy(self.assets)
        changed[0]['reverse_users'] = []
        self.assertTrue(any(('reverse dependency mismatch' in error for error in registry_errors(changed))))

    def test_dependency_cycle_rejected(self):
        changed = copy.deepcopy(self.assets)
        changed[0]['dependencies'] = [changed[0]['name']]
        self.assertTrue(any(('cycle' in error for error in registry_errors(changed))))

    def test_unproven_verified_status_rejected(self):
        changed = copy.deepcopy(self.assets)
        changed[0]['status'] = 'verified'
        self.assertTrue(any(('verified without evidence' in error for error in registry_errors(changed))))

    def test_html_parser_collects_link_targets(self):
        parser = PageParser()
        parser.feed('<h1>Title</h1><a href="missing.html#x">Go</a><script src="local.js"></script>')
        self.assertEqual(parser.links, ['missing.html#x'])
        self.assertEqual(parser.resources, ['local.js'])

    def test_missing_link_and_duplicate_html_id_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / 'manual'
            shutil.copytree(ROOT, fixture, ignore=shutil.ignore_patterns('__pycache__', '.git'))
            home = fixture / 'index.html'
            home.write_text(home.read_text(encoding='utf-8').replace('</main>', '<a href="absent-test-target.html">Missing</a><div id="main">Duplicate</div></main>'), encoding='utf-8')
            report = validate(fixture)
            self.assertTrue(any(('missing target absent-test-target.html' in error for error in report['errors'])))
            self.assertTrue(any(('duplicate IDs' in error for error in report['errors'])))

    def test_later_creation_dependency_rejected(self):
        changed = copy.deepcopy(self.assets)
        changed[0]['dependencies'] = ['EEquipmentSlot']
        self.assertTrue(any(('later dependency' in error for error in registry_errors(changed))))

    def test_population_policy(self):
        self.assertEqual([targets(population)['optional'] for population in [1, 2, 5, 10, 30]], [10, 12, 14, 16, 18])
        with self.assertRaises(TypeError):
            targets(2.5)

    def test_source_accounting_passes_but_completion_fails(self):
        self.assertEqual(check()['status'], 'pass')
        self.assertEqual(check(True)['status'], 'fail')
if __name__ == '__main__':
    unittest.main()
