"""Regression checks for readable, reproducible HTML publication."""
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_data_inventory import Document, inventory_page, load_registry, navigation
from html_format import format_html_documents


class Links(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.links = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs))


class HTMLFormatTests(unittest.TestCase):
    def test_html_is_indented_and_idempotent_without_changing_preformatted_text(self):
        code = 'first  line\n    second line\n'
        source = '<main><h1 id="title">Title</h1><pre>' + code + '</pre></main>'
        documents = {'guide/example.html': source, 'data/example.json': '{"unchanged":true}'}
        formatted = format_html_documents(documents)
        self.assertIn('\n  <h1 id="title">Title</h1>\n', formatted['guide/example.html'])
        preformatted = re.search(r'<pre>(.*?)</pre>', formatted['guide/example.html'], re.S)[1]
        # HTML ignores one newline immediately after an opening pre tag.
        self.assertEqual(code, preformatted.removeprefix('\n'))
        self.assertEqual(documents['data/example.json'], formatted['data/example.json'])
        self.assertEqual(formatted, format_html_documents(formatted))

    def test_navigation_handles_wrapped_attributes_and_closing_tags_without_duplicates(self):
        source = ('<nav><a\n class="nav-home" href="../index.html">Overview</a\n>'
                  '<a\n data-roadmap-nav href="old.html">Roadmap</a\n>'
                  '<div><p>Catalogs</p><a\n data-inventory-nav href="old.html">Data</a\n></div></nav>')
        first = format_html_documents({'guide/example.html': navigation(source, 'guide/example.html')})
        second = format_html_documents({'guide/example.html': navigation(first['guide/example.html'], 'guide/example.html')})
        self.assertEqual(first, second)
        links = Links(first['guide/example.html']).links
        self.assertEqual(['development-roadmap.html'], [a['href'] for a in links if 'data-roadmap-nav' in a])
        self.assertEqual(['data-inventory.html'], [a['href'] for a in links if 'data-inventory-nav' in a])

    def test_wrapped_heading_text_has_stable_review_metadata(self):
        document = Document('<main><h1>Long\n  heading</h1><h2 id="section">Another\n heading</h2></main>')
        self.assertEqual([('h1', None, 'Long heading'), ('h2', 'section', 'Another heading')], document.headings)

    def test_inventory_keeps_its_metadata_with_a_formatted_template(self):
        source = inventory_page(load_registry(), (ROOT / 'guide/networking.html').read_text())
        self.assertIn('<title>Data Inventory · MMORPG Reference v2</title>', source)
        self.assertIn('content="Canonical data definitions, reviewed decisions and future Briarwake implementation work."', source)

    def test_missing_node_reports_the_required_setup(self):
        with patch('html_format.subprocess.run', side_effect=FileNotFoundError):
            with self.assertRaisesRegex(RuntimeError, 'install Node.js and run npm ci'):
                format_html_documents({'guide/missing-node.html': '<main>Missing Node fixture</main>'})


if __name__ == '__main__':
    unittest.main()
