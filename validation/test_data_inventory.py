"""Regression checks for catalog integrity and preservation of published content."""
from __future__ import annotations

import copy
import json
import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_data_inventory import (CATEGORIES, DATA_START, INVENTORY_PAGE, content_fingerprint,
                                  expected_outputs, load_registry, stale_outputs, validate_registry)


class Element:
    def __init__(self, tag, attrs, parent=None):
        self.tag = tag
        self.attrs = dict(attrs)
        self.parent = parent
        self.children = []


class Tree(HTMLParser):
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self, source):
        super().__init__()
        self.root = Element('document', [])
        self.stack = [self.root]
        self.elements = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        node = Element(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        self.elements.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break


class InventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_registry()

    def rejected(self, registry, message):
        self.assertTrue(any(message in error for error in validate_registry(registry)), message)

    def test_registry_and_generated_output_are_current(self):
        self.assertEqual([], validate_registry(self.registry))
        self.assertEqual([], stale_outputs(expected_outputs(self.registry)))

    def test_duplicate_identifiers_and_case_insensitive_names_are_rejected(self):
        registry = copy.deepcopy(self.registry)
        registry['entries'][1]['id'] = registry['entries'][0]['id']
        registry['entries'][1]['name'] = registry['entries'][0]['name'].lower()
        self.rejected(registry, 'Duplicate inventory identifiers')
        self.rejected(registry, 'Duplicate inventory names')

    def test_unmanaged_entry_fields_and_invalid_categories_are_rejected(self):
        for key in ('fields', 'properties', 'values', 'methods', 'inherits', 'default', 'example'):
            registry = copy.deepcopy(self.registry)
            registry['entries'][0][key] = []
            self.rejected(registry, 'invalid canonical entry metadata')
        registry['entries'][0]['category'] = 'Class'
        self.rejected(registry, 'exactly Enum, Interface and Schema')

    def test_definition_status_must_agree_with_open_decisions(self):
        registry = copy.deepcopy(self.registry)
        issue = registry['review_issues'][0]
        issue['state'] = 'open'
        issue['completion_criteria'] = ['Resolve the test decision.']
        entry = next(e for e in registry['entries'] if e['name'] in issue['entries'])
        entry['review_issues'] = [issue['id']]
        entry['review_status'] = 'Needs Review'
        entry['definition_status'] = 'Fully Defined'
        entry['definition_extent'] = 'Partial'
        self.rejected(registry, 'decision status and definition extent disagree')

    def test_missing_evidence_paths_and_anchors_are_rejected(self):
        for reference in ('guide/missing-page.html#main', 'guide/combat.html#missing-section'):
            registry = copy.deepcopy(self.registry)
            registry['entries'][0]['evidence'].append(reference)
            self.rejected(registry, 'missing')

    def test_feature_associations_require_section_evidence(self):
        registry = copy.deepcopy(self.registry)
        registry['entries'][0]['feature_pages'].append('guide/glossary.html')
        self.rejected(registry, 'every feature association must have section evidence')
        self.rejected(registry, 'missing or excluded feature page')

    def test_removed_page_review_and_changed_content_are_rejected(self):
        registry = copy.deepcopy(self.registry)
        registry['pages'].pop()
        self.rejected(registry, 'review every source HTML page')
        registry = copy.deepcopy(self.registry)
        registry['pages'][0]['reviewed_content_sha256'] = 'outdated'
        self.rejected(registry, 'feature content changed')

    def test_review_issues_and_backlinks_are_required(self):
        registry = copy.deepcopy(self.registry)
        entry = registry['entries'][0]
        entry['review_issues'] = ['missing-issue']
        self.rejected(registry, 'invalid review issue')

    def test_exact_section_membership_hierarchy_and_bottom_placement(self):
        for page in self.registry['pages']:
            source = (ROOT / page['page']).read_text()
            tree = Tree(source)
            sections = [node for node in tree.elements if node.attrs.get('class') == 'data-inventory']
            expected = [e for e in self.registry['entries'] if page['page'] in e['feature_pages']]
            with self.subTest(page=page['page']):
                self.assertEqual(1 if expected else 0, len(sections))
                if not expected:
                    continue
                section = sections[0]
                self.assertEqual('article-body', section.parent.attrs.get('class'))
                self.assertIs(section, section.parent.children[-1])
                self.assertEqual(('h2', 'data'), (section.children[0].tag, section.children[0].attrs.get('id')))
                actual = [node.attrs['data-inventory-id'] for node in tree.elements if 'data-inventory-id' in node.attrs]
                self.assertCountEqual([e['id'] for e in expected], actual)
                self.assertEqual(len(actual), len(set(actual)))
                self.assertEqual(page['reviewed_content_sha256'], content_fingerprint(source))
                self.assertEqual(1, source.count(DATA_START))

    def test_inventory_categories_are_sorted_and_searchable(self):
        source = (ROOT / INVENTORY_PAGE).read_text()
        tree = Tree(source)
        for category, plural in CATEGORIES.items():
            table = next(node for node in tree.elements if node.attrs.get('id') == 'inventory-' + plural.lower())
            tbody = next(node for node in table.children if node.tag == 'tbody')
            expected = [e['id'] for e in sorted(self.registry['entries'], key=lambda e: e['name'].casefold()) if e['category'] == category]
            self.assertEqual(expected, [node.attrs['id'] for node in tbody.children])
        search = json.loads((ROOT / 'assets/search-index.js').read_text().removeprefix('window.SEARCH_INDEX=').strip().removesuffix(';'))
        destinations = {r['url'] for r in search if r.get('source') == 'data-inventory'}
        for entry in self.registry['entries']:
            self.assertIn(INVENTORY_PAGE + '#' + entry['id'], destinations)

    def test_owned_output_is_idempotent_and_stale_changes_are_detected(self):
        first = expected_outputs(self.registry)
        self.assertEqual(first, expected_outputs(self.registry))
        corrupted = dict(first)
        corrupted[INVENTORY_PAGE] += '<p>outdated</p>'
        self.assertIn(INVENTORY_PAGE, stale_outputs(corrupted))
        for page in self.registry['pages']:
            self.assertEqual(page['reviewed_content_sha256'], content_fingerprint(first[page['page']]))


if __name__ == '__main__':
    unittest.main()
