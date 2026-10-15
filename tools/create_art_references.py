"""Generate original, grid-built study artwork; never read purchased artwork."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from pixel_art import Raster, aseprite, rgba

ROOT = Path(__file__).resolve().parents[1]
BASE = 'art-style/assets/'
PALETTE = json.loads((ROOT / 'sources/art-bible/palette.json').read_text())
COLORS = {c['name']: c['hex'] for c in PALETTE['colors']}


def ramp(name):
    return [COLORS[item] for item in PALETTE['ramps'][name]]


FAMILIES = ['grass', 'dirt', 'packed-earth', 'mud', 'stone', 'cobblestone', 'sand', 'snow', 'forest-ground', 'marsh-ground']
MATERIALS = ['grass', 'earth', 'earth', 'leather', 'stone', 'stone', 'earth', 'metal', 'leaves', 'grass']


def terrain(family, variant=0):
    index = FAMILIES.index(family)
    colors = ramp(MATERIALS[index])
    base = colors[3] if family in {'sand', 'snow'} else colors[1 if family in {'mud', 'forest-ground', 'marsh-ground'} else 2]
    tile = Raster(16, 16, base)
    clusters = [(3, 4, 3, 1), (10, 10, 2, 1), (6, 13, 2, 1)]
    for n, (x, y, w, h) in enumerate(clusters):
        x, y = (x + variant * 5) % 12 + 1, (y + variant * 3) % 12 + 1
        tile.rect(x, y, w, h, colors[1 if n % 2 else 2])
        if family in {'grass', 'forest-ground', 'marsh-ground'}:
            tile.pixel(x + 1, y - 1, colors[2])
    if family == 'cobblestone':
        for row in range(0, 16, 8):
            for col in range(-4 if row else 0, 16, 8):
                tile.rect(col + 1, row + 1, 7, 6, colors[1])
                tile.rect(col + 2, row + 1, 5, 4, colors[2])
                tile.line(col + 2, row + 1, col + 6, row + 1, colors[3])
    return tile


def masks():
    result = []
    for value in range(256):
        valid = True
        for diagonal, first, second in [(2, 1, 4), (8, 4, 16), (32, 16, 64), (128, 64, 1)]:
            if value & diagonal and not (value & first and value & second):
                valid = False
        if valid:
            result.append(value)
    return result


MASKS = masks()


def transition(tile, mask):
    image = Raster(16, 16)
    for y in range(16):
        for x in range(16):
            nx, ny = x, y
            left, top = x < 8, y < 8
            horizontal = bool(mask & (64 if left else 4))
            vertical = bool(mask & (1 if top else 16))
            diagonal = bool(mask & (128 if left and top else 2 if top else 32 if left else 8))
            if not left:
                nx = 15 - nx
            if not top:
                ny = 15 - ny
            fill = True
            if not horizontal and nx < 3:
                fill = False
            if not vertical and ny < 3:
                fill = False
            if horizontal and vertical and not diagonal and nx + ny < 4:
                fill = False
            if not horizontal and not vertical and nx + ny < 9:
                fill = False
            if fill:
                image.pixel(x, y, tile.pixel(x, y))
    return image


def building_piece(kind):
    image = Raster(16, 16)
    wood, brick, stone, metal = ramp('wood'), ramp('brick'), ramp('stone'), ramp('metal')
    if kind.startswith('roof'):
        image.rect(0, 0, 16, 16, brick[0])
        for y in range(0, 16, 4):
            image.rect(0, y, 16, 3, brick[2])
            for x in range(-4 if y % 8 else 0, 16, 8):
                image.line(x + 1, y, x + 7, y, brick[3])
                image.pixel(x, y + 2, brick[1])
        if kind == 'roof-left':
            image.rect(0, 0, 2, 16, wood[0])
            image.rect(2, 0, 1, 16, wood[2])
        if kind == 'roof-right':
            image.rect(13, 0, 3, 16, wood[0])
        if kind == 'roof-ridge':
            image.rect(0, 0, 16, 3, wood[0])
            image.rect(0, 1, 16, 1, wood[3])
        if kind == 'roof-eave':
            image.rect(0, 12, 16, 4, wood[0])
            image.rect(0, 12, 16, 1, wood[2])
    elif kind in {'wall', 'wall-corner', 'door', 'window', 'foundation', 'beam', 'shutter'}:
        image.rect(0, 0, 16, 16, '#b4b4a0')
        image.rect(0, 0, 16, 2, wood[1])
        image.rect(0, 12, 16, 4, wood[0])
        image.rect(0, 12, 16, 1, wood[2])
        if kind in {'wall-corner', 'beam'}:
            image.rect(0, 0, 3, 16, wood[1])
            image.rect(1, 1, 1, 14, wood[3])
        if kind == 'door':
            image.rect(3, 1, 10, 15, wood[0])
            image.rect(4, 2, 8, 14, wood[1])
            image.line(7, 3, 7, 14, wood[0])
            image.pixel(10, 9, ramp('fire')[2])
        if kind in {'window', 'shutter'}:
            image.rect(3, 3, 10, 8, wood[0])
            image.rect(4, 4, 8, 6, ramp('water')[0])
            image.rect(7, 4, 1, 6, wood[2])
            image.rect(4, 6, 8, 1, wood[2])
        if kind == 'foundation':
            image.rect(0, 0, 16, 16, stone[1])
            for y in [0, 8]:
                image.line(0, y, 15, y, stone[0])
                image.line(2 if y else 10, y, 2 if y else 10, y + 7, stone[0])
    elif kind in {'fence', 'pillar', 'sign', 'chimney', 'stairs', 'bridge', 'bridge-broken'}:
        if kind.startswith('bridge'):
            for y in range(1, 16, 4):
                image.rect(0, y, 16, 3, wood[2])
                image.line(0, y, 15, y, wood[3])
            image.rect(1, 0, 2, 16, wood[0])
            image.rect(13, 0, 2, 16, wood[0])
            if kind == 'bridge-broken':
                image.rect(4, 4, 8, 8, (0, 0, 0, 0))
        if kind == 'fence':
            image.rect(0, 5, 16, 2, wood[2])
            image.rect(0, 11, 16, 2, wood[1])
            image.rect(3, 2, 3, 14, wood[0])
            image.rect(3, 2, 1, 14, wood[3])
        if kind == 'sign':
            image.rect(7, 5, 2, 11, wood[0])
            image.rect(1, 1, 14, 8, wood[0])
            image.rect(2, 2, 12, 5, wood[2])
            image.rect(5, 3, 6, 1, wood[3])
        if kind in {'pillar', 'chimney'}:
            image.rect(4, 0, 8, 16, stone[0])
            image.rect(4, 1, 6, 15, stone[2])
            for y in [4, 9, 14]:
                image.line(4, y, 11, y, stone[1])
        if kind == 'stairs':
            image.rect(0, 0, 16, 16, stone[1])
            for y in range(0, 16, 4):
                image.rect(0, y, 16, 1, stone[3])
                image.rect(0, y + 3, 16, 1, stone[0])
    return image


PIECES = ['roof-left', 'roof', 'roof-right', 'roof-ridge', 'roof-eave', 'wall', 'wall-corner', 'foundation', 'door', 'window', 'chimney', 'shutter', 'beam', 'pillar', 'stairs', 'fence', 'sign', 'bridge', 'bridge-broken']


def tree(kind='deciduous'):
    image = Raster(48, 64)
    leaf, wood = ramp('leaves'), ramp('wood')
    image.ellipse(8, 52, 34, 9, ramp('grass')[0])
    image.polygon([(19, 58), (21, 27), (28, 27), (30, 57), (35, 60), (27, 59), (24, 56), (18, 60)], wood[0])
    image.rect(22, 28, 5, 29, wood[1])
    image.rect(22, 35, 2, 19, wood[2])
    if kind == 'dead':
        for x, y in [(11, 22), (35, 17), (7, 34), (40, 29)]:
            image.line(24, y + 12, x, y, wood[0])
            image.line(x, y, x, y - 7, wood[1])
        return image
    if kind == 'evergreen':
        for y, width in [(4, 18), (14, 28), (26, 38)]:
            image.polygon([(24, y), (24 + width // 2, y + 20), (24, y + 18), (24 - width // 2, y + 20)], leaf[0])
            image.polygon([(23, y + 2), (24 + width // 2 - 4, y + 16), (24 - width // 2 + 2, y + 16)], leaf[2])
            image.line(23, y + 3, 18, y + 12, leaf[3])
    else:
        for x, y, w, h in [(3, 15, 28, 27), (18, 17, 28, 29), (10, 3, 28, 31), (1, 24, 26, 23), (23, 26, 23, 21)]:
            image.ellipse(x, y, w, h, leaf[0])
            image.ellipse(x + 1, y + 1, w - 4, h - 5, leaf[1])
            image.ellipse(x + 2, y + 1, w - 7, h - 9, leaf[2])
            image.ellipse(x + 4, y + 2, w // 2, 5, leaf[3])
    return image


def prop(kind):
    image = Raster(32, 32)
    leaf, wood, stone = ramp('leaves'), ramp('wood'), ramp('stone')
    if kind in {'rock', 'ore', 'stump', 'log'}:
        colors = wood if kind in {'stump', 'log'} else stone
        image.ellipse(3, 22, 26, 8, ramp('grass')[0])
        image.polygon([(4, 25), (7, 16), (17, 12), (26, 18), (28, 26), (20, 29), (8, 28)], colors[0])
        image.polygon([(6, 24), (8, 17), (17, 14), (24, 19), (24, 25), (17, 27)], colors[2])
        image.line(9, 18, 16, 15, colors[3])
        image.polygon([(18, 16), (25, 20), (24, 26), (18, 26)], colors[1])
        if kind == 'ore':
            for x, y in [(11, 22), (20, 19), (17, 25)]:
                image.rect(x, y, 3, 2, ramp('metal')[3])
        if kind == 'stump':
            image.ellipse(8, 14, 17, 7, wood[3])
            image.line(13, 17, 20, 17, wood[1])
    elif kind in {'bush', 'berry', 'herb', 'flowers', 'grass', 'reeds', 'mushroom', 'roots', 'vine'}:
        image.ellipse(5, 25, 23, 5, ramp('grass')[0])
        if kind in {'bush', 'berry'}:
            for x, y in [(5, 18), (12, 13), (19, 18)]:
                image.ellipse(x, y, 11, 12, leaf[0])
                image.ellipse(x, y, 9, 7, leaf[2])
                image.line(x + 2, y + 1, x + 5, y + 1, leaf[3])
            if kind == 'berry':
                for x, y in [(9, 22), (17, 18), (23, 24)]:
                    image.rect(x, y, 2, 2, ramp('danger')[2])
        else:
            for x, y in [(9, 18), (16, 12), (22, 17)]:
                image.line(x, 27, x + 1, y, leaf[1])
                image.line(x, 25, x - 4, y + 3, leaf[2])
                if kind in {'flowers', 'herb', 'mushroom'}:
                    image.rect(x - 1, y, 4, 2, ramp('magic' if kind == 'herb' else 'fire')[3])
                if kind == 'reeds':
                    image.rect(x, y - 5, 2, 6, wood[2])
    return image


DIRECTIONS = ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw']


def character(direction='s', frame=0):
    body, outfit, hair, weapon = [Raster(64, 64) for _ in range(4)]
    skin, cloth, dark, wood = ramp('skin'), ramp('cloth'), ramp('metal')[0], ramp('wood')
    facing = {'n': (0, -1), 'ne': (1, -1), 'e': (1, 0), 'se': (1, 1), 's': (0, 1), 'sw': (-1, 1), 'w': (-1, 0), 'nw': (-1, -1)}[direction]
    dx, dy = facing
    bob = [0, -1, 0, 0, -1, 0][frame]
    stride = [-2, -1, 0, 2, 1, 0][frame]
    cy = 20 + bob
    body.ellipse(27, cy - 3, 11, 11, dark)
    body.ellipse(28, cy - 2, 9, 9, skin[2])
    body.rect(29, cy, 3, 3, skin[3])
    if dx:
        body.rect(36 if dx > 0 else 26, cy + (0 if dy < 0 else 3), 2, 3, skin[2])
    if dy >= 0:
        eyes = [29, 34] if dx == 0 else [34 if dx > 0 else 29]
        for x in eyes:
            body.pixel(x + dx, cy + 3, dark)
    body.rect(30, cy + 8, 5, 3, skin[1])
    body.rect(28, 31 + bob, 9, 9, skin[2])
    leg_x = [28, 34] if abs(dx) != 1 or dy else [30, 33]
    for i, x in enumerate(leg_x):
        length = stride if i else -stride
        body.rect(x, 39, 3, 7 + length // 2, dark)
        body.rect(x - (1 if dx < 0 else 0), 45 + length // 2, 4, 2, wood[0])
    shoulder_left = 26 + (2 if dx > 0 else 0)
    shoulder_right = 38 - (2 if dx < 0 else 0)
    outfit.polygon([(29 + dx, 28 + bob), (35 + dx, 28 + bob), (shoulder_right, 32 + bob), (37, 40), (27, 40), (shoulder_left, 32 + bob)], cloth[0])
    outfit.polygon([(29 + dx, 29 + bob), (34 + dx, 29 + bob), (35, 38), (28, 38)], cloth[2])
    outfit.rect(29, 30 + bob, 2, 5, cloth[3])
    outfit.rect(27, 38, 10, 2, wood[1])
    for i, x in enumerate([shoulder_left, shoulder_right - 2]):
        sy = 32 + bob + (stride // 2 if i else -stride // 2)
        outfit.rect(x, sy, 3, 6, cloth[1 if i else 2])
        body.rect(x, sy + 5, 3, 3, skin[2])
    hair.ellipse(27, cy - 3, 11, 5, wood[0])
    hair.ellipse(28, cy - 3, 8, 3, wood[2])
    if dy < 0:
        hair.rect(28, cy, 8, 6, wood[1])
        hair.rect(29, cy, 2, 4, wood[2])
    else:
        hair.rect(27, cy, 2, 4, wood[1])
        hair.rect(36, cy, 2, 4, wood[0])
    wx, wy = (40 if dx >= 0 else 22), 36 + (stride // 2)
    weapon.line(wx, wy - 9, wx + dx * 3, wy + 2, dark)
    weapon.line(wx, wy - 8, wx + dx * 3, wy, ramp('metal')[2])
    weapon.line(wx - 2, wy + 1, wx + 3, wy + 1, wood[2])
    weapon.line(wx, wy + 2, wx, wy + 5, wood[0])
    return [body, outfit, hair, weapon]


def composite(layers):
    image = Raster(layers[0].width, layers[0].height)
    for layer in layers:
        image.paste(layer, 0, 0)
    return image


def icon(kind):
    image = Raster(16, 16)
    wood, metal, leaf = ramp('wood'), ramp('metal'), ramp('leaves')
    if kind in {'sword', 'tool', 'arrow'}:
        image.line(4, 13, 12, 3, metal[0])
        image.line(5, 12, 12, 4, metal[2])
        image.line(6, 11, 12, 5, metal[3])
        image.line(3, 10, 7, 13, wood[2])
        image.line(2, 14, 4, 12, wood[1])
        if kind == 'tool':
            image.line(6, 2, 14, 7, metal[1])
    elif kind in {'potion', 'quest', 'currency'}:
        image.rect(6, 2, 4, 3, wood[1])
        image.ellipse(3, 5, 10, 9, metal[0])
        image.ellipse(4, 6, 8, 7, ramp('magic' if kind == 'potion' else 'fire')[2])
        image.rect(5, 6, 2, 3, metal[3])
    elif kind in {'food', 'fish'}:
        image.ellipse(2, 5, 11, 7, wood[0])
        image.ellipse(3, 5, 9, 5, ramp('water' if kind == 'fish' else 'earth')[3])
        if kind == 'fish':
            image.polygon([(10, 8), (15, 4), (15, 12)], ramp('water')[2])
            image.pixel(4, 7, metal[0])
    elif kind in {'ore', 'wood'}:
        image.polygon([(2, 12), (4, 5), (10, 2), (14, 10), (11, 14)], metal[0])
        image.polygon([(3, 11), (5, 6), (10, 3), (12, 9), (10, 12)], wood[2] if kind == 'wood' else metal[2])
        image.line(6, 5, 9, 4, metal[3])
    else:
        image.line(7, 14, 9, 3, leaf[1])
        image.ellipse(2, 5, 7, 4, leaf[2])
        image.ellipse(8, 2, 6, 4, leaf[3])
    return image


def build_outputs():
    outputs, records = {}, []

    def save(name, image, category, rule, status='Proposed reference', source='tools/create_art_references.py', **extra):
        path = BASE + name + '.png'
        outputs[path] = image.png()
        records.append({'id': name, 'path': path, 'category': category, 'dimensions': [image.width, image.height], 'palette': PALETTE['id'], 'status': status, 'source': source, 'attribution': 'Original procedural pixel study created for Briarwake Art Bible; no third-party pixels or references ingested.', 'rules': rule, 'sha256': hashlib.sha256(outputs[path]).hexdigest(), **extra})
        return image

    atlas = Raster(256, 256)
    cells = {}
    for row, family in enumerate(FAMILIES):
        for variant in range(3):
            tile = terrain(family, variant)
            atlas.paste(tile, variant * 16, row * 16)
            cells[f'{family}-{variant}'] = [variant, row]
    water = Raster(16, 16, ramp('water')[1])
    water.line(2, 5, 7, 5, ramp('water')[2])
    water.line(9, 12, 13, 12, ramp('water')[2])
    for i in range(4):
        tile = Raster(16, 16, ramp('water')[1])
        tile.line(2 + i, 5, 7 + i, 5, ramp('water')[2])
        tile.line(8 - i, 12, 12 - i, 12, ramp('water')[2])
        atlas.paste(tile, (4 + i) * 16, 0)
        cells[f'water-{i}'] = [4 + i, 0]
    for i, kind in enumerate(PIECES):
        x, y = 4 + i % 12, 2 + i // 12
        atlas.paste(building_piece(kind), x * 16, y * 16)
        cells[kind] = [x, y]
    save('atlas', atlas, 'tileset', '16×16 cells; 256×256 atlas; margin 0; spacing 0; unused cells transparent.', 'Technical demonstration', cells=cells)
    save('tile-grass', terrain('grass'), 'terrain', '16×16; quiet value range; grouped blades.')
    repeat = Raster(160, 160)
    for y in range(10):
        for x in range(10):
            repeat.paste(terrain('grass'), x * 16, y * 16)
    save('repeat-10', repeat, 'terrain', 'Ten by ten identical tiles: inspect repeating clusters at native size.', 'Technical demonstration')
    repeat3 = Raster(48, 48)
    for y in range(3):
        for x in range(3):
            repeat3.paste(terrain('grass'), x * 16, y * 16)
    save('repeat-3', repeat3, 'terrain', 'Three by three exact repeat.', 'Technical demonstration')
    transition_atlas = Raster(256, 480)
    transition_cells = {}
    for row, family in enumerate(FAMILIES):
        for i, mask in enumerate(MASKS):
            x, y = i % 16, row * 3 + i // 16
            transition_atlas.paste(transition(terrain(family), mask), x * 16, y * 16)
            transition_cells[f'{family}:{mask}'] = [x, y]
    save('transitions', transition_atlas, 'transition', '47 canonical gated neighbor masks for each of ten families. Last slot in each 48-cell family is empty.', 'Technical demonstration', masks=MASKS, cells=transition_cells)
    objects = {kind: tree(kind) for kind in ['deciduous', 'evergreen', 'dead']}
    objects.update({kind: prop(kind) for kind in ['rock', 'ore', 'stump', 'log', 'bush', 'berry', 'herb', 'flowers', 'grass', 'reeds', 'mushroom', 'roots', 'vine']})
    for kind, image in objects.items():
        save(kind, image, 'vegetation' if kind not in {'rock', 'ore'} else 'resource', 'Ground anchor at center x, bottom minus 4; trunk collision separate from canopy.')

    maps = {}

    def scene(name, region, crowded=0):
        width, height = 24, 16
        ground = []
        water_cells = set()
        for y in range(height):
            for x in range(width):
                family = {'mountain': 'stone', 'marsh': 'marsh-ground', 'coast': 'sand', 'ruins': 'forest-ground'}.get(region, 'grass')
                if region == 'forest':
                    family = 'forest-ground'
                if abs(x - (18 + (y // 4) % 2)) < (3 if region == 'coast' else 1) or (region == 'marsh' and y in {3, 4, 12} and x > 13):
                    ground.append({'tile': 'water-0', 'at': [x, y]})
                    water_cells.add((x, y))
                else:
                    if y in {9, 10} or x in {11, 12}:
                        family = 'packed-earth' if region not in {'ruins', 'mountain'} else 'cobblestone'
                    ground.append({'tile': f'{family}-{(x * 3 + y * 7) % 3}', 'at': [x, y]})
        overlays = []
        for y in range(height):
            for x in range(width):
                if (x, y) in water_cells:
                    continue
                neighbors = [(0, -1, 1), (1, -1, 2), (1, 0, 4), (1, 1, 8), (0, 1, 16), (-1, 1, 32), (-1, 0, 64), (-1, -1, 128)]
                mask = sum(bit for dx, dy, bit in neighbors if (x + dx, y + dy) not in water_cells)
                for diagonal, first, second in [(2, 1, 4), (8, 4, 16), (32, 16, 64), (128, 64, 1)]:
                    if not (mask & first and mask & second):
                        mask &= ~diagonal
                if mask != 255:
                    cell = next(c for c in ground if c['at'] == [x, y])
                    family = cell['tile'].rsplit('-', 1)[0]
                    overlays.append({'family': family, 'mask': mask, 'at': [x, y]})
        placements = []
        house_origins = [(2, 2), (10, 2)] if name == 'village' else [(2, 3)] if name == 'village-second' else []
        for hx, hy in house_origins:
            for ry in range(3):
                for rx in range(5):
                    kind = 'roof-ridge' if ry == 0 else 'roof-eave' if ry == 2 else 'roof-left' if rx == 0 else 'roof-right' if rx == 4 else 'roof'
                    placements.append({'tile': kind, 'at': [hx + rx, hy + ry]})
            for rx in range(5):
                placements.append({'tile': 'door' if rx == 2 else 'window' if rx in {1, 3} else 'wall-corner', 'at': [hx + rx, hy + 3]})
                placements.append({'tile': 'stairs' if rx == 2 else 'foundation', 'at': [hx + rx, hy + 4]})
            placements.append({'tile': 'chimney', 'at': [hx + 3, hy]})
            placements.append({'tile': 'sign', 'at': [hx + 5, hy + 4]})
        if region == 'ruins':
            for rx in range(3, 9):
                placements.append({'tile': 'foundation', 'at': [rx, 4]})
            for rx in [3, 8]:
                for ry in range(2, 5):
                    placements.append({'tile': 'pillar', 'at': [rx, ry]})
        if region == 'mountain':
            for rx in range(3, 11):
                for ry in [2, 3]:
                    placements.append({'tile': 'foundation', 'at': [rx, ry]})
            placements.extend({'tile': 'stairs', 'at': [7, ry]} for ry in [2, 3])
        for x in [17, 18, 19]:
            placements.append({'tile': 'bridge', 'at': [x, 9]})
        natural = []
        positions = [(1, 1), (7, 0), (14, 1), (0, 6), (7, 6), (21, 3), (2, 12), (6, 13), (14, 12), (21, 12), (23, 6)]
        if region == 'forest':
            positions += [(3, 0), (5, 2), (9, 0), (15, 4), (0, 11), (3, 14), (9, 13), (23, 13)]
        for i, (x, y) in enumerate(positions):
            kind = 'evergreen' if region == 'mountain' else 'dead' if region == 'marsh' else 'rock' if region == 'coast' else 'deciduous'
            if i % 4 == 3:
                kind = 'ore' if region == 'mountain' else 'bush'
            natural.append({'object': kind, 'at': [x * 16, y * 16]})
        for i in range(16):
            px, py = (i * 43 + 9) % 350, (i * 31 + 17) % 220
            if any(px + 32 > hx * 16 and px < (hx + 5) * 16 and py + 32 > hy * 16 and py < (hy + 5) * 16 for hx, hy in house_origins):
                continue
            natural.append({'object': 'reeds' if region == 'marsh' else 'herb' if region == 'forest' else 'flowers', 'at': [px, py]})
        actors = [{'facing': DIRECTIONS[i % 8], 'at': [((i * 41 + 150) % 280) + 30, ((i * 19 + 130) % 110) + 120]} for i in range(crowded or 1)]
        recipe = {'id': name, 'region': region, 'grid': [width, height], 'cell': [16, 16], 'ground': ground, 'shore_overlays': overlays, 'modules': placements, 'objects': natural, 'actors': actors, 'source_atlas': BASE + 'atlas.png', 'transition_atlas': BASE + 'transitions.png', 'status': 'Proposed reference'}
        maps[name] = recipe
        return render_scene(recipe, atlas, transition_atlas, objects)

    for name, region in [('village', 'settlement'), ('village-second', 'settlement'), ('forest-scene', 'forest'), ('mountain-scene', 'mountain'), ('marsh-scene', 'marsh'), ('coast-scene', 'coast'), ('ruins-scene', 'ruins')]:
        save(name, scene(name, region), 'region', 'Assembled from named atlas cells and reusable objects; exact map recipe is downloadable.')
    for count in [1, 2, 5, 12, 30]:
        image = scene(f'crowd-{count}', 'settlement', count)
        for i in range(min(count, 8)):
            image.ellipse(130 + i * 13, 145 + i % 2 * 9, 18, 6, ramp('magic')[1])
            image.line(134 + i * 13, 146 + i % 2 * 9, 142 + i * 13, 146 + i % 2 * 9, ramp('magic')[3])
        save(f'crowd-{count}', image, 'readability', f'{count} local actors; static composition stress study, not runtime or gameplay approval.', 'Technical demonstration')
    base_scene = scene('lighting-base', 'settlement')
    lighting = {'day': (1, 1, 1), 'dusk': (0.9, 0.72, 0.75), 'night': (0.48, 0.57, 0.76), 'rain': (0.72, 0.79, 0.82), 'snow': (0.93, 0.98, 1.08), 'torchlight': (0.66, 0.55, 0.55)}
    for weather, factors in lighting.items():
        image = Raster(384, 256)
        for y in range(256):
            for x in range(384):
                color = base_scene.pixel(x, y)
                factor = factors
                if weather == 'torchlight' and (x - 140) ** 2 + (y - 133) ** 2 < 42 ** 2:
                    factor = (1.25, 1.03, 0.7)
                image.pixel(x, y, tuple(min(255, int(color[c] * factor[c])) for c in range(3)) + (color[3],))
        if weather == 'rain':
            for i in range(90):
                x, y = (i * 47) % 384, (i * 29) % 256
                image.line(x, y, x - 1, y + 3, ramp('water')[2])
        if weather == 'snow':
            for i in range(70):
                image.rect((i * 47) % 384, (i * 29) % 256, 2, 1, ramp('metal')[3])
        save('light-' + weather, image, 'lighting', 'Identical map under illustrative color treatment; derived colors are lighting previews, not master-palette additions.', 'Technical demonstration')
    frames = [character(direction, frame) for direction in DIRECTIONS for frame in range(6)]
    sheet = Raster(384, 512)
    frame_data = []
    for i, layers in enumerate(frames):
        sheet.paste(composite(layers), (i % 6) * 64, (i // 6) * 64)
        frame_data.append({'filename': f'walk_{DIRECTIONS[i // 6]}_{i % 6:03d}', 'frame': {'x': i % 6 * 64, 'y': i // 6 * 64, 'w': 64, 'h': 64}, 'duration': 100, 'sourceSize': {'w': 64, 'h': 64}, 'spriteSourceSize': {'x': 0, 'y': 0, 'w': 64, 'h': 64}, 'trimmed': False, 'rotated': False})
    source_path = 'art-style/templates/character-study.aseprite'
    outputs[source_path] = aseprite(['body', 'outfit', 'hair', 'equipment_front'], frames, [100] * 48, [(f'walk_{direction}', i * 6, i * 6 + 5) for i, direction in enumerate(DIRECTIONS)])
    save('character-walk', sheet, 'animation', 'Original eight-facing study, six frames each; rows N NE E SE S SW W NW. Not measured purchased art.', source=source_path, frame_size=[64, 64], frame_count=48, origin=[32, 48])
    outputs[BASE + 'character-walk.json'] = (json.dumps({'frames': frame_data, 'meta': {'image': 'character-walk.png', 'size': {'w': 384, 'h': 512}, 'scale': '1', 'frameTags': [{'name': f'walk_{d}', 'from': i * 6, 'to': i * 6 + 5, 'direction': 'forward'} for i, d in enumerate(DIRECTIONS)]}}, indent=2) + '\n').encode()
    layers = character('s')
    for name, image in zip(['body', 'outfit', 'hair', 'equipment'], layers):
        save('layer-' + name, image, 'customization', 'Shared untrimmed 64×64 frame; origin (32,48).', 'Technical demonstration', source=source_path)
    save('character', composite(layers), 'character', 'Approximately 32 visible pixels in a 64×64 frame.', source=source_path)
    diagrams = Raster(320, 80)
    for i in range(4):
        image = composite(layers[:i + 1])
        diagrams.paste(image, i * 64, 0)
    save('paper-doll', diagrams.crop(0, 0, 256, 64), 'customization', 'Four progressive assemblies: body, outfit, hair, equipment.', 'Technical demonstration')
    bad = composite(layers[:3])
    bad.paste(layers[3], 5, -4)
    diagrams.paste(bad, 256, 0)
    save('paper-doll-comparison', diagrams, 'customization', 'Body, outfit, hair, equipment; fifth cell demonstrates incorrect equipment shift.', 'Technical demonstration')
    save('registration-bad', bad, 'customization', 'Weapon shifted five pixels right and four up; reject.', 'Incorrect example')
    icons = Raster(160, 32)
    for i, kind in enumerate(['sword', 'tool', 'potion', 'food', 'fish', 'ore', 'wood', 'herb', 'quest', 'currency']):
        icons.paste(icon(kind), i * 16, 0)
    save('icons', icons, 'icons', '16×16 cells; common top-left light; category silhouette before ornament.')
    creature = Raster(64, 64)
    fur = ramp('leather')
    creature.ellipse(16, 41, 35, 7, ramp('grass')[0])
    creature.polygon([(16, 33), (22, 26), (39, 27), (47, 34), (44, 41), (22, 40)], fur[0])
    creature.polygon([(18, 33), (23, 28), (38, 29), (44, 34), (40, 38), (22, 37)], fur[2])
    creature.line(24, 29, 35, 29, fur[3])
    for x in [22, 37]:
        creature.rect(x, 37, 4, 8, fur[0])
    creature.polygon([(12, 28), (15, 18), (21, 24), (27, 25), (28, 34), (20, 38), (10, 34)], fur[0])
    creature.polygon([(14, 28), (17, 24), (24, 27), (24, 33), (18, 35), (12, 32)], fur[1])
    creature.pixel(18, 28, ramp('fire')[3])
    creature.polygon([(44, 30), (55, 25), (53, 33), (44, 36)], fur[1])
    save('creature', creature, 'creature', 'Original small quadruped silhouette study; not a canonical species or approved enemy.')
    effect_frames = []
    effect_sheet = Raster(384, 64)
    for i in range(6):
        effect = Raster(64, 64)
        radius = 4 + i * 4
        for y in range(64):
            for x in range(64):
                distance = (x - 32) ** 2 + (y - 32) ** 2
                if (radius - 2) ** 2 <= distance <= radius ** 2 and (i < 3 or (x + y) % 7 < 4):
                    effect.pixel(x, y, ramp('magic')[3 if i < 2 else 2 if i < 4 else 1])
        effect_frames.append([effect])
        effect_sheet.paste(effect, i * 64, 0)
    outputs['art-style/templates/magic-ring-study.aseprite'] = aseprite(['effect_front'], effect_frames, [60, 60, 80, 100, 100, 120], [('heal_release', 0, 5)])
    save('magic-ring', effect_sheet, 'effects', 'Six 64×64 frames: open-ring activation and broken recovery preserve the actor center.', source='art-style/templates/magic-ring-study.aseprite', frame_size=[64, 64], frame_count=6)
    variants = Raster(320, 64)
    for i, material in enumerate(['leather', 'earth', 'leaves', 'wood', 'cloth']):
        variant_layers = character('s')
        original_ramp = [rgba(c) for c in ramp('cloth')]
        new_ramp = ramp(material)
        for y in range(64):
            for x in range(64):
                color = variant_layers[1].pixel(x, y)
                if color in original_ramp:
                    variant_layers[1].pixel(x, y, new_ramp[original_ramp.index(color)])
        if i in {0, 1, 3}:
            variant_layers[1].rect(29, 33, 6, 8, ramp('leather' if i != 1 else 'cloth')[2])
        variants.paste(composite(variant_layers), i * 64, 0)
    save('vocation-outfits', variants, 'outfits', 'Five proposed material/apron variants in Forgekeeper, Hearthkeeper, Wayfinder, Woodwright, Apothecary order. Themes, not mandatory equipped cosmetics.')
    boundary_test = Raster(256, 160)
    field = {(x, y) for y in range(10) for x in range(16) if x in {5, 6} or y in {4, 5} or (x in {11, 12} and y in {1, 2})}
    for y in range(10):
        for x in range(16):
            boundary_test.paste(terrain('grass', (x + y) % 3), x * 16, y * 16)
            if (x, y) not in field:
                continue
            mask = sum(bit for dx, dy, bit in [(0,-1,1),(1,-1,2),(1,0,4),(1,1,8),(0,1,16),(-1,1,32),(-1,0,64),(-1,-1,128)] if (x + dx, y + dy) in field)
            for diagonal, a, b in [(2,1,4),(8,4,16),(32,16,64),(128,64,1)]:
                if not (mask & a and mask & b):
                    mask &= ~diagonal
            boundary_test.paste(transition(terrain('dirt'), mask), x * 16, y * 16)
    save('path-crossing', boundary_test, 'transition', 'A two-cell crossing, concave and convex corners, and an isolated patch assembled from the documented 47-mask family.', 'Technical demonstration')
    materials = Raster(192, 48)
    for i, material in enumerate(PALETTE['ramps']):
        x, y = i % 8 * 24, i // 8 * 24
        colors = ramp(material)
        materials.ellipse(x + 3, y + 3, 18, 18, colors[0])
        materials.ellipse(x + 4, y + 4, 15, 14, colors[1])
        materials.ellipse(x + 4, y + 4, 12, 10, colors[2])
        materials.rect(x + 7, y + 5, 5, 2, colors[3])
    save('materials', materials, 'materials', 'Four-step ramps in palette order; spheres are technical light-placement studies.', 'Technical demonstration')
    comparisons = Raster(192, 64)
    comparisons.paste(tree(), 0, 0)
    noisy = tree()
    for y in range(64):
        for x in range(48):
            if noisy.pixel(x, y)[3] and (x * 17 + y * 31) % 5 < 2:
                noisy.pixel(x, y, ramp('leaves')[(x * 7 + y) % 4])
    comparisons.paste(noisy, 48, 0)
    original_tree = tree()
    for y in range(64):
        for x in range(48):
            c = original_tree.pixel(x // 2, y // 2)
            comparisons.pixel(x + 96, y, c)
    for y in range(64):
        for x in range(48):
            if (x - 24) ** 2 / 300 + (y - 30) ** 2 / 800 < 1:
                comparisons.pixel(x + 144, y, (20 + y, 55 + y, 35 + y, 255))
    save('technique-comparison', comparisons, 'comparison', 'Left to right: grouped foliage; isolated noise; doubled internal pixel density; excessive continuous gradient.', 'Technical demonstration')
    states = Raster(64, 32)
    for x in range(4):
        states.paste(water, x * 16, 0)
        states.paste(building_piece('bridge-broken' if x < 2 else 'bridge'), x * 16, 0)
    save('bridge-states', states, 'living-region', 'Two 32×32 state canvases; shared origin (16,16); broken center changes traversal only after gameplay approval.', 'Technical demonstration')
    module_preview = Raster(128, 96)
    for i, piece in enumerate(PIECES):
        module_preview.paste(building_piece(piece), i % 8 * 16, i // 8 * 16)
    save('building-pieces', module_preview, 'architecture', 'Named reusable 16×16 roof, wall, foundation, detail and bridge modules.', 'Technical demonstration')
    for template, size in [('terrain-16', 16), ('icon-16', 16), ('icon-32', 32), ('prop-64', 64), ('building-128', 128), ('effect-64', 64)]:
        frames_template = [[Raster(size, size)] for _ in range(4 if template == 'effect-64' else 1)]
        outputs[f'art-style/templates/{template}.aseprite'] = aseprite(['art'], frames_template, [100] * len(frames_template))
    outputs['art-style/templates/atlas-study.aseprite'] = aseprite(['terrain_and_modules'], [[atlas]], [100])
    outputs['art-style/templates/transitions-study.aseprite'] = aseprite(['terrain_transitions'], [[transition_atlas]], [100])
    outputs['sources/art-bible/scene-maps.json'] = (json.dumps(maps, indent=2) + '\n').encode()
    outputs[BASE + 'briarwake-study.gpl'] = ('GIMP Palette\nName: Briarwake Study 01 — Proposed\nColumns: 4\n# No owner palette approval recorded\n' + '\n'.join(' '.join(str(v) for v in c['rgb']) + ' ' + c['name'] for c in PALETTE['colors']) + '\n').encode()
    for record in records:
        record['source_sha256'] = hashlib.sha256(outputs[record['source']] if record['source'] in outputs else (ROOT / record['source']).read_bytes()).hexdigest()
    manifest = {'version': '0.1.0', 'date': '2026-10-15', 'palette': PALETTE['id'], 'rights': 'Original documentation reference studies. Owner review required before production use. No third-party license is granted or inferred.', 'assets': records, 'templates': [{'path': p, 'sha256': hashlib.sha256(data).hexdigest(), 'status': 'Technical demonstration', 'validation': 'Binary structure checked; opening and export in Aseprite pending'} for p, data in outputs.items() if p.endswith('.aseprite')]}
    outputs['sources/art-bible/references.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    return outputs


def render_scene(recipe, atlas, transition_atlas, objects):
    image = Raster(recipe['grid'][0] * 16, recipe['grid'][1] * 16)
    cells = {}
    for row, family in enumerate(FAMILIES):
        for variant in range(3):
            cells[f'{family}-{variant}'] = [variant, row]
    cells['water-0'] = [4, 0]
    cells.update({kind: [4 + i % 12, 2 + i // 12] for i, kind in enumerate(PIECES)})
    for cell in recipe['ground']:
        x, y = cells[cell['tile']]
        image.paste(atlas.crop(x * 16, y * 16, 16, 16), cell['at'][0] * 16, cell['at'][1] * 16)
    for cell in recipe['shore_overlays']:
        x, y = cell['at']
        image.paste(atlas.crop(64, 0, 16, 16), x * 16, y * 16)
        index = MASKS.index(cell['mask'])
        tx, ty = index % 16, FAMILIES.index(cell['family']) * 3 + index // 16
        image.paste(transition_atlas.crop(tx * 16, ty * 16, 16, 16), x * 16, y * 16)
    for cell in recipe['modules']:
        x, y = cells[cell['tile']]
        image.paste(atlas.crop(x * 16, y * 16, 16, 16), cell['at'][0] * 16, cell['at'][1] * 16)
    sorted_objects = [(item['at'][1] + objects[item['object']].height - 4, objects[item['object']], item['at']) for item in recipe['objects']]
    sorted_objects.extend((actor['at'][1], composite(character(actor['facing'])), [actor['at'][0] - 32, actor['at'][1] - 48]) for actor in recipe['actors'])
    for _, sprite, position in sorted(sorted_objects, key=lambda item: item[0]):
        image.paste(sprite, *position)
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    stale = []
    for path, data in build_outputs().items():
        destination = ROOT / path
        if args.check:
            if not destination.exists() or destination.read_bytes() != data:
                stale.append(path)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
    if stale:
        print('Stale reference outputs: ' + ', '.join(stale))
        return 1
    print('PASS: original reference outputs ' + ('are current' if args.check else 'generated'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
