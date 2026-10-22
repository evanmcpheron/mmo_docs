"""Selection is bounded; unsupported PR claims fail visibly."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from validate import FULL_CHECKS, ROOT, changed_files, commands, main, select_checks, input_identity
from check_sources import check_sources


class SelectionTests(unittest.TestCase):
    def test_roadmap_edit_checks_current_graph_without_regression_suite_or_browser(self):
        impact = select_checks(['sources/development-roadmap.json'])
        self.assertEqual([], impact['tests'])
        self.assertEqual([], impact['unresolved'])
        plan = dict(commands('quick', impact, ['sources/development-roadmap.json']))
        self.assertEqual({'whitespace', 'staged-whitespace', 'sources'}, set(plan))
        self.assertNotIn('freshness', plan['sources'])
        self.assertNotIn('site', plan['sources'])
        gate = dict(commands('quick', impact, ['sources/development-roadmap.json'], gate=True))
        self.assertIn('freshness', gate['sources'])
        self.assertNotIn('aggregate', gate)
        self.assertNotIn('browser', gate)

    def test_contract_and_gameplay_data_select_real_invariants_but_not_unrelated_allocations(self):
        for path in ('data/recipes.json', 'data/abilities.json'):
            impact = select_checks([path])
            self.assertIn('contracts', impact['checks'])
            self.assertNotIn('allocations', impact['checks'])
            self.assertIn('data-structure', dict(commands('quick', impact, [path], gate=True))['data'])
        impact = select_checks(['data/character_catalog.json'])
        self.assertIn('allocations', impact['checks'])
        self.assertIn('data', dict(commands('quick', impact, ['data/character_catalog.json'], gate=True))['data'])

    def test_unknown_inputs_block_pr_claim_without_local_full_fallback(self):
        impact = select_checks(['mystery.bin'])
        self.assertTrue(impact['unresolved'])
        self.assertEqual({'whitespace', 'staged-whitespace'}, set(dict(commands('quick', impact, ['mystery.bin']))))
        with patch('validate.changed_files', return_value=(['mystery.bin'], 'base')), redirect_stdout(io.StringIO()):
            self.assertEqual(2, main(['--gate', '--explain']))

    def test_default_empty_scope_and_failed_git_are_quick(self):
        for arguments in (['--explain'], ['--mode', 'fast', '--explain']):
            stream = io.StringIO()
            with patch('validate.changed_files', side_effect=ValueError('missing base')), redirect_stdout(stream):
                self.assertEqual(0, main(arguments))
            self.assertIn('executing QUICK', stream.getvalue())
            self.assertIn('Cannot establish Git scope', stream.getvalue())
            self.assertNotIn('aggregate:', stream.getvalue())
        with patch('validate.changed_files', side_effect=ValueError('missing base')), redirect_stdout(io.StringIO()):
            self.assertEqual(2, main(['--gate', '--explain']))
        self.assertEqual([], select_checks([])['checks'])

    def test_validator_changes_select_importing_regressions_not_tests_for_content_edits(self):
        impact = select_checks(['validation/check_development_roadmap.py'])
        self.assertIn('test_development_roadmap', impact['tests'])
        self.assertEqual([], select_checks(['README.txt'])['tests'])

    def test_ui_requires_browser_mode_and_static_ticket_updates_do_not(self):
        impact = select_checks(['assets/styles.css'])
        self.assertIn('browser', impact['checks'])
        self.assertNotIn('browser', dict(commands('quick', impact, ['assets/styles.css'], gate=True)))
        self.assertIn('browser', dict(commands('integration', impact, ['assets/styles.css'], gate=True)))
        with patch('validate.changed_files', return_value=(['assets/styles.css'], 'base')), redirect_stdout(io.StringIO()):
            self.assertEqual(2, main(['--gate', '--explain']))

    def test_full_retains_comprehensive_gates_and_native_is_unsupported(self):
        self.assertEqual(set(FULL_CHECKS), set(dict(commands('full', {'checks': [], 'tests': []}, []))))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(2, main(['--mode', 'native']))

    def test_missing_tool_is_failure_and_successful_unchanged_stages_are_not_duplicated(self):
        with patch('validate.changed_files', return_value=(['README.txt'], 'base')), \
             patch('validate.subprocess.run', side_effect=FileNotFoundError('missing prerequisite')), \
             patch('validate.input_identity', return_value='fixture'), \
             patch('validate.subprocess.check_output', return_value='revision'), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(1, main([]))
        plan = commands('quick', select_checks(['sources/development-roadmap.json']), ['sources/development-roadmap.json'], gate=True)
        self.assertEqual(len(plan), len({name for name, _ in plan}))
        self.assertEqual(1, sum(name == 'sources' for name, _ in plan))

    def test_malformed_changed_json_is_rejected_without_generation(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.git') as directory:
            root = Path(directory)
            (root / 'invalid.json').write_text('{')
            self.assertTrue(check_sources([], ['invalid.json'], root))
            (root / 'invalid.json').write_text('{}')
            self.assertEqual([], check_sources([], ['invalid.json'], root))

    def test_changed_content_during_validation_cannot_pass(self):
        with patch('validate.changed_files', return_value=(['README.txt'], 'base')), \
             patch('validate.input_identity', side_effect=['before', 'after']), \
             patch('validate.subprocess.run', return_value=subprocess.CompletedProcess([], 0)), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(1, main([]))

    def test_missing_links_and_anchors_fail_static_checks_without_chrome(self):
        from run_checks import site_checks
        with tempfile.TemporaryDirectory(dir=ROOT / '.git') as directory:
            root = Path(directory)
            (root / 'assets').mkdir()
            (root / 'assets/search-index.js').write_text('window.SEARCH_INDEX=[];')
            page = root / 'index.html'
            page.write_text('<a href="missing.html#criterion">Missing</a>')
            with patch('run_checks.ROOT', root):
                self.assertTrue(any(not item['passed'] for item in site_checks()))
                page.write_text('<a href="#absent">Missing anchor</a>')
                self.assertTrue(any(not item['passed'] for item in site_checks()))
                page.write_text('<p id="present">Valid</p><a href="#present">Valid</a>')
                self.assertTrue(all(item['passed'] for item in site_checks()))

    def test_archived_details_are_not_reread_unless_changed_but_current_inputs_remain_identified(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.git') as directory:
            root = Path(directory)
            def git(*arguments):
                return subprocess.check_output(['git', *arguments], cwd=root, stderr=subprocess.PIPE)
            git('init', '-q', '-b', 'main')
            archive = root / 'validation/epics/example/raw.log'
            archive.parent.mkdir(parents=True)
            archive.write_text('historical details')
            source = root / 'source.json'
            source.write_text('{}')
            git('add', '.')
            before = input_identity(root)
            archive.write_text('other historical details')
            self.assertEqual(before, input_identity(root))
            self.assertNotEqual(before, input_identity(root, ['validation/epics/example/raw.log']))
            source.write_text('{"changed": true}')
            self.assertNotEqual(before, input_identity(root))

    def test_shared_template_changes_select_browser_and_node_regressions_are_not_browser_tests(self):
        for path in ('scripts/build_development_roadmap.py', 'scripts/build_data_inventory.py', 'scripts/html_format.py'):
            self.assertIn('browser', select_checks([path])['checks'])
        impact = select_checks(['validation/test_browser_cleanup.mjs'])
        self.assertNotIn('browser', impact['checks'])
        plan = dict(commands('quick', impact, ['validation/test_browser_cleanup.mjs']))
        self.assertIn('browser-cleanup', plan)
        self.assertNotIn('browser', plan)


class ChangedFileTests(unittest.TestCase):
    def test_commits_index_worktree_untracked_deletions_and_renames_are_all_detected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.git') as directory:
            root = Path(directory)

            def git(*args):
                return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.STDOUT)

            git('init', '-q', '-b', 'main')
            git('config', 'user.name', 'Validation fixture')
            git('config', 'user.email', 'validation@example.invalid')
            for name in ('committed', 'staged', 'unstaged', 'deleted', 'renamed', 'reverted'):
                (root / name).write_text('base\n')
            git('add', '.')
            git('commit', '-qm', 'base fixture')
            base = git('rev-parse', 'HEAD').decode().strip()
            git('switch', '-qc', 'task')
            (root / 'committed').write_text('branch change\n')
            git('commit', '-qam', 'task fixture')
            git('switch', '-q', 'main')
            (root / 'main-only').write_text('main advanced\n')
            git('add', 'main-only')
            git('commit', '-qm', 'advanced main fixture')
            git('switch', '-q', 'task')
            (root / 'staged').write_text('staged change\n')
            (root / 'reverted').write_text('staged change\n')
            git('add', 'staged', 'reverted')
            (root / 'reverted').write_text('base\n')
            (root / 'unstaged').write_text('local change\n')
            (root / 'deleted').unlink()
            git('mv', 'renamed', 'renamed with\nnewline')
            (root / 'untracked space').write_text('new file\n')
            paths, revision = changed_files(root, 'main')
            self.assertEqual(base, revision)
            self.assertEqual({'committed', 'staged', 'unstaged', 'deleted', 'renamed',
                              'renamed with\nnewline', 'untracked space', 'reverted'}, set(paths))
            self.assertNotIn('main-only', paths)
            with self.assertRaises(subprocess.CalledProcessError):
                changed_files(root, 'missing-ref')


if __name__ == '__main__':
    unittest.main()
