"""Behavioral coverage for the tracked engine implementation boundary."""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from check_engine_artifacts import legacy_engine_artifacts, main


class EngineArtifactTests(unittest.TestCase):
    def test_rejects_legacy_projects_scripts_shaders_scenes_resources_and_cache(self):
        paths = ['project.godot', 'nested/PROJECT.GODOT', 'src/player.gd', 'src/player.gdc',
                 'assets/water.gdshader', 'assets/common.gdshaderinc', 'native/game.gdextension',
                 'scenes/world.tscn', 'assets/settings.tres', '.godot/imported/texture.bin',
                 'validation/evidence/player.gd']
        self.assertEqual(sorted(paths), legacy_engine_artifacts(paths))

    def test_historical_documentation_and_unreal_log_mentions_are_allowed(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', directory], check=True)
            documents = {
                'guide/roadmap.html': 'Historical Godot runs cannot substantiate native completion.',
                'sources/roadmap.json': '{"note": "No GDScript gameplay implementation is claimed."}',
                'validation/evidence/engine.log': (
                    'LogDesktopPlatform: Found project "/Documents/Godot/briarwake/ReferenceExport.uproject" '
                    'in recently opened files'),
                'validation/evidence/game-readme.md': 'The older Godot project remains separate.',
                'guide/godot-migration.html': 'Unreal Engine 5 native C++ is the implementation target.',
            }
            for name, text in documents.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            subprocess.run(['git', '-C', directory, 'add', '.'], check=True)
            with redirect_stdout(StringIO()) as output:
                self.assertEqual(0, main(root))
            self.assertIn('artifact count: 0', output.getvalue())

    def test_audit_rejects_tracked_artifacts_and_preserves_git_path_boundaries(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', directory], check=True)
            tracked = 'legacy ü\nscene.tscn'
            (root / tracked).write_text('[gd_scene format=3]')
            (root / 'untracked.gd').write_text('extends Node')
            with redirect_stdout(StringIO()):
                self.assertEqual(0, main(root))
            subprocess.run(['git', '-C', directory, 'add', '--', tracked], check=True)
            with redirect_stdout(StringIO()) as output:
                self.assertEqual(1, main(root))
            self.assertIn(tracked, output.getvalue())
            self.assertNotIn('untracked.gd', output.getvalue())


if __name__ == '__main__':
    unittest.main()
