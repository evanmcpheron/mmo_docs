"""Scope selection must fail closed and include committed and local task changes."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from validate import (CONTRACT_TESTS, FULL_CHECKS, ROADMAP_TESTS, ROOT, changed_files,
                      commands, main, select_checks)


class SelectionTests(unittest.TestCase):
    def test_roadmap_inputs_and_generated_pages_require_link_inventory_and_browser_checks(self):
        for path in ('sources/development-roadmap.json', 'sources/roadmap-audit.html.inc',
                     'sources/roadmap-reuse-review.html.inc',
                     'guide/roadmap-bw-001.html', 'guide/development-roadmap.html'):
            with self.subTest(path=path):
                mode, tests, checks = select_checks([path])
                self.assertEqual('fast', mode)
                self.assertEqual(ROADMAP_TESTS, set(tests))
                self.assertTrue({'html-format', 'aggregate', 'browser', 'engine-artifacts'} <= set(checks))

    def test_contracts_and_schema_outputs_require_model_regressions_and_browser(self):
        for path in ('sources/data-inventory.json', 'sources/data-model.schema.json',
                     'guide/data-inventory.html', 'validation/data-model-review.txt'):
            with self.subTest(path=path):
                mode, tests, checks = select_checks([path])
                self.assertEqual('fast', mode)
                self.assertEqual(CONTRACT_TESTS, set(tests))
                self.assertIn('aggregate', checks)
                self.assertIn('browser', checks)

    def test_shipped_records_check_models_and_all_outputs_without_launching_browser(self):
        for path in ('data/character_catalog.json', 'data/abilities.json', 'data/races.json'):
            with self.subTest(path=path):
                mode, tests, checks = select_checks([path])
                self.assertEqual('fast', mode)
                self.assertEqual(CONTRACT_TESTS, set(tests))
                self.assertIn('aggregate', checks)
                self.assertNotIn('browser', checks)

    def test_shared_generated_outputs_and_combined_changes_union_their_dependencies(self):
        for paths in (['assets/search-index.js'], ['data/manifest.json'],
                      ['sources/development-roadmap.json', 'sources/data-inventory.json']):
            mode, tests, checks = select_checks(paths)
            self.assertEqual('fast', mode)
            self.assertEqual(ROADMAP_TESTS | CONTRACT_TESTS, set(tests))
            self.assertIn('browser', checks)

    def test_generated_search_does_not_require_unrelated_domain_tests_when_its_source_is_known(self):
        for paths in (['sources/data-inventory.json', 'assets/search-index.js'],
                      ['assets/search-index.js', 'sources/data-inventory.json']):
            mode, tests, checks = select_checks(paths)
            self.assertEqual('fast', mode)
            self.assertEqual(CONTRACT_TESTS, set(tests))
            self.assertIn('aggregate', checks)
            self.assertIn('browser', checks)

    def test_unknown_infrastructure_templates_and_browser_dependencies_fall_back_to_full(self):
        for path in ('new-file.json', 'data/new-catalog.json', 'AGENTS.md', 'README.txt',
                     '.agents/skills/execute-ticket/SKILL.md', 'validation/validate.py',
                     'validation/check_data_inventory.py', 'validation/run_checks.py',
                     'validation/test_data_model.py', 'validation/browser_cleanup.mjs',
                     'validation/check_inventory_browser.mjs', '.github/workflows/validate-documentation.yml',
                     'scripts/data_model.py', 'scripts/build_data_inventory.py',
                     'scripts/build_development_roadmap.py', 'guide/networking.html',
                     'guide/combat.html', 'assets/styles.css', 'assets/app.js'):
            with self.subTest(path=path):
                self.assertEqual('full', select_checks(['sources/development-roadmap.json', path])[0])

    def test_missing_dependency_registry_and_empty_scope_fall_back_to_full(self):
        self.assertEqual('full', select_checks([])[0])
        with tempfile.TemporaryDirectory(dir=ROOT / '.git') as directory:
            self.assertEqual('full', select_checks(['data/abilities.json'], Path(directory))[0])

    def test_full_plan_contains_every_existing_gate_and_no_duplicate_standalone_checks(self):
        plan = dict(commands('full', [], FULL_CHECKS))
        self.assertEqual(set(FULL_CHECKS), set(plan))
        self.assertEqual(['npm', 'run', 'format:check'], plan['html-format'])
        self.assertIn('validation/run_checks.py', plan['aggregate'])
        self.assertIn('--read-only', plan['aggregate'])
        self.assertNotIn('--scope', plan['aggregate'])
        self.assertIn('discover', plan['python'])
        self.assertIn('validation/test_browser_cleanup.mjs', plan['browser-cleanup'])
        self.assertIn('validation/check_inventory_browser.mjs', plan['browser'])
        self.assertIn('--screenshots', plan['browser'])
        self.assertIn('validation/check_engine_artifacts.py', plan['engine-artifacts'])

    def test_unspecified_mode_is_full_and_fast_scope_is_never_reported_as_full_success(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(0, main(['--explain']))
        self.assertIn('executing FULL', output.getvalue())
        output = io.StringIO()
        with patch('validate.changed_files', return_value=(['data/abilities.json'], 'fixture-base')):
            with redirect_stdout(output):
                self.assertEqual(0, main(['--mode', 'fast', '--explain']))
        self.assertIn('executing FAST', output.getvalue())
        self.assertIn('Deferred to FULL: browser-cleanup, browser', output.getvalue())

    def test_failed_git_detection_falls_back_to_full(self):
        with patch('validate.changed_files', side_effect=ValueError('no merge base')):
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(0, main(['--mode', 'fast', '--explain']))
        self.assertIn('executing FULL', output.getvalue())
        self.assertIn('Changed-file detection failed', output.getvalue())

    def test_allocation_checks_are_deferred_only_when_their_shipped_data_inputs_are_unchanged(self):
        for path, defer in (('sources/development-roadmap.json', True),
                            ('sources/data-inventory.json', True), ('data/character_catalog.json', False),
                            ('data/allocation_examples.json', False), ('data/talents.json', False)):
            with self.subTest(path=path):
                output = io.StringIO()
                with patch('validate.changed_files', return_value=([path], 'fixture-base')):
                    with redirect_stdout(output):
                        self.assertEqual(0, main(['--mode', 'fast', '--explain']))
                self.assertEqual(defer, '--scope documentation' in output.getvalue())
                if defer:
                    self.assertIn('unchanged data inputs', output.getvalue())

    def test_missing_executables_fail_every_affected_stage_and_return_nonzero(self):
        with patch('validate.subprocess.run', side_effect=FileNotFoundError('missing prerequisite')):
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(1, main(['--mode', 'full']))
        for name in FULL_CHECKS:
            self.assertIn('FAIL ' + name, output.getvalue())
        self.assertIn('FULL FAIL', output.getvalue())


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
