"""Regressions for incomplete terrain families and misleading source/export evidence."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pixel_art import Raster, aseprite, read_png
from validate_art_bible import inspect_aseprite, validate_palette, Parser
from create_art_references import masks, terrain, transition, render_scene

ROOT = Path(__file__).resolve().parents[2]


class ArtBibleTests(unittest.TestCase):
    def test_palette_rgb_and_approval_cannot_drift(self):
        palette = json.loads((ROOT / 'sources/art-bible/palette.json').read_text())
        self.assertEqual(validate_palette(palette), [])
        changed = copy.deepcopy(palette)
        changed['colors'][0]['rgb'][0] += 1
        changed['colors'][1]['approval_status'] = 'Approved production reference'
        errors = validate_palette(changed)
        self.assertTrue(any('RGB mismatch' in e for e in errors))
        self.assertTrue(any('no owner record' in e for e in errors))

    def test_diagonals_require_both_cardinal_neighbors(self):
        result = masks()
        self.assertEqual(len(result), 47)
        self.assertIn(0, result)
        self.assertIn(255, result)
        self.assertNotIn(2, result)
        self.assertNotIn(3, result)
        self.assertIn(7, result)

    def test_full_transition_retains_base_and_isolated_patch_opens_edges(self):
        base = terrain('grass')
        self.assertEqual(transition(base, 255).pixels, base.pixels)
        patch = transition(base, 0)
        self.assertEqual(patch.pixel(0, 0)[3], 0)
        self.assertEqual(patch.pixel(8, 8)[3], 255)

    def test_png_crc_corruption_is_rejected(self):
        data = bytearray(Raster(16, 16, '#123456').png())
        data[-5] ^= 1
        with self.assertRaises(ValueError):
            read_png(data)

    def test_aseprite_source_keeps_layers_frames_duration_and_tags(self):
        frames = [[Raster(64, 64), Raster(64, 64, '#123456')], [Raster(64, 64, '#654321'), Raster(64, 64)]]
        data = aseprite(['body', 'outfit'], frames, [90, 120], [('walk_s', 0, 1)])
        source = inspect_aseprite(data)
        self.assertEqual(source['dimensions'], [64, 64])
        self.assertEqual(source['layers'], ['body', 'outfit'])
        self.assertEqual(source['durations'], [90, 120])
        self.assertEqual(source['tags'], [{'name': 'walk_s', 'from': 0, 'to': 1}])
        self.assertEqual(source['frames'][1][0], frames[1][0].pixels)
        with self.assertRaises(ValueError):
            inspect_aseprite(data[:-10])

    def test_complete_original_transition_atlas_has_all_families(self):
        refs = json.loads((ROOT / 'sources/art-bible/references.json').read_text())
        atlas = next(a for a in refs['assets'] if a['id'] == 'transitions')
        self.assertEqual(len(atlas['cells']), 470)
        self.assertEqual(len(set(tuple(p) for p in atlas['cells'].values())), 470)

    def test_unapproved_new_references_do_not_inherit_style_approval(self):
        refs = json.loads((ROOT / 'sources/art-bible/references.json').read_text())
        self.assertTrue(all(a['status'] in {'Proposed reference', 'Technical demonstration', 'Incorrect example'} for a in refs['assets']))

    def test_semantic_controls_and_alt_are_checked(self):
        parser = Parser()
        parser.feed('<button>Click</button><img src="x.png">')
        self.assertEqual(len(parser.errors), 2)

    def test_two_villages_reconstruct_from_the_same_exported_components(self):
        maps = json.loads((ROOT / 'sources/art-bible/scene-maps.json').read_text())
        atlas = read_png((ROOT / maps['village']['source_atlas']).read_bytes())
        transitions = read_png((ROOT / maps['village']['transition_atlas']).read_bytes())
        names = {o['object'] for key in ['village', 'village-second'] for o in maps[key]['objects']}
        objects = {name: read_png((ROOT / ('art-style/assets/' + name + '.png')).read_bytes()) for name in names}
        self.assertEqual(maps['village']['source_atlas'], maps['village-second']['source_atlas'])
        self.assertNotEqual(maps['village']['modules'], maps['village-second']['modules'])
        for name in ['village', 'village-second']:
            actual = read_png((ROOT / ('art-style/assets/' + name + '.png')).read_bytes())
            self.assertEqual(render_scene(maps[name], atlas, transitions, objects).pixels, actual.pixels)


if __name__ == '__main__':
    unittest.main()
