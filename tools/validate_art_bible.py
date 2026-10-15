"""Validate original Art Bible sources, local exports and publication contracts."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import struct
from urllib.parse import unquote, urlsplit
import zlib
from art_manual import art_pages, read
from pixel_art import read_png

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {'Approved production reference', 'Approved creative direction', 'Proposed reference', 'Technical demonstration', 'Incorrect example'}


class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.resources, self.errors = [], [], [], []
        self.h1 = 0

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'h1':
            self.h1 += 1
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        if tag in {'img', 'script', 'source', 'iframe'} and 'src' in attrs:
            self.resources.append(attrs['src'])
        if tag == 'link' and 'href' in attrs:
            self.resources.append(attrs['href'])
        if tag == 'img' and not attrs.get('alt') and attrs.get('aria-hidden') != 'true':
            self.errors.append('Image missing alt text')
        if tag == 'button' and attrs.get('type') != 'button':
            self.errors.append('Button missing explicit type')


def inspect_aseprite(data):
    if len(data) < 128:
        raise ValueError('Truncated Aseprite header')
    length, magic, count, width, height, depth = struct.unpack_from('<IHHHHH', data)
    if length != len(data) or magic != 0xA5E0 or depth != 32 or not width or not height or not count:
        raise ValueError('Invalid Aseprite header')
    position, layers, frames, durations, tags = 128, [], [], [], []
    for frame_index in range(count):
        frame_length, frame_magic, chunk_count, duration = struct.unpack_from('<IHHH', data, position)
        if frame_magic != 0xF1FA or duration <= 0 or frame_length < 16:
            raise ValueError('Invalid Aseprite frame')
        end = position + frame_length
        cursor, cels = position + 16, {}
        for _ in range(chunk_count):
            size, kind = struct.unpack_from('<IH', data, cursor)
            if size < 6 or cursor + size > end:
                raise ValueError('Invalid Aseprite chunk size')
            body = data[cursor + 6:cursor + size]
            if kind == 0x2004:
                string_length = struct.unpack_from('<H', body, 16)[0]
                layers.append(body[18:18 + string_length].decode())
            if kind == 0x2005:
                layer, x, y, opacity, cel_type = struct.unpack_from('<HhhBH', body)
                cw, ch = struct.unpack_from('<HH', body, 16)
                if cel_type != 2 or (cw, ch, x, y, opacity) != (width, height, 0, 0, 255):
                    raise ValueError('Unexpected reference cel layout')
                pixels = zlib.decompress(body[20:])
                if len(pixels) != cw * ch * 4 or layer >= len(layers):
                    raise ValueError('Invalid reference cel pixels')
                cels[layer] = pixels
            if kind == 0x2018:
                number = struct.unpack_from('<H', body)[0]
                tpos = 10
                for _ in range(number):
                    first, last = struct.unpack_from('<HH', body, tpos)
                    string_length = struct.unpack_from('<H', body, tpos + 17)[0]
                    name = body[tpos + 19:tpos + 19 + string_length].decode()
                    if not (0 <= first <= last < count) or not name:
                        raise ValueError('Invalid animation tag')
                    tags.append({'name': name, 'from': first, 'to': last})
                    tpos += 19 + string_length
            cursor += size
        if cursor != end or len(cels) != len(layers):
            raise ValueError('Aseprite frame has missing data')
        frames.append(cels)
        durations.append(duration)
        position = end
    if position != len(data):
        raise ValueError('Aseprite trailing or missing frames')
    return {'dimensions': [width, height], 'layers': layers, 'frames': frames, 'durations': durations, 'tags': tags}


def validate_palette(palette):
    errors = []
    names = [c.get('name') for c in palette.get('colors', [])]
    if len(names) != len(set(names)):
        errors.append('Duplicate palette name')
    for color in palette.get('colors', []):
        value = color.get('hex', '')
        if not re.fullmatch('#[0-9a-fA-F]{6}', value):
            errors.append('Invalid palette hex: ' + str(color.get('name')))
            continue
        if color.get('rgb') != [int(value[n:n + 2], 16) for n in (1, 3, 5)]:
            errors.append('Palette RGB mismatch: ' + color['name'])
        if color.get('approval_status') not in STATUSES or not all(color.get(k) for k in ['primary_usage', 'secondary_usage', 'material']):
            errors.append('Missing palette metadata: ' + color['name'])
        if color.get('approval_status', '').startswith('Approved') and not palette.get('owner_approval'):
            errors.append('Palette approval has no owner record')
    for name, members in palette.get('ramps', {}).items():
        if not 3 <= len(members) <= 5 or not set(members) <= set(names):
            errors.append('Invalid palette ramp: ' + name)
    return errors


def validate(root=ROOT, reference_tree=None, check_generated=True):
    errors = []
    chapters = read(root, 'chapters')
    pages = chapters['pages']
    manifest = read(root, 'references')
    palette = read(root, 'palette')
    errors.extend(validate_palette(palette))
    records = manifest['assets']
    assets = {a['id']: a for a in records}
    for key in ['id', 'path']:
        if len({a[key] for a in records}) != len(records):
            errors.append('Duplicate reference ' + key)
    paths = [p['path'] for p in pages]
    if len(set(paths)) != len(paths) or not paths or paths[0] != 'art-style/index.html':
        errors.append('Missing homepage or duplicate page path')
    parsed = {}
    known = {i['path'] for i in json.loads(reference_tree.read_text())['tree'] if i['type'] == 'blob'} if reference_tree else set()
    for page in pages:
        path = root / page['path']
        if not path.is_file():
            errors.append('Missing page: ' + page['path'])
            continue
        parser = Parser()
        parser.feed(path.read_text())
        parsed[path.resolve()] = parser
        errors.extend(page['path'] + ': ' + e for e in parser.errors)
        if parser.h1 != 1 or len(parser.ids) != len(set(parser.ids)):
            errors.append('Heading or duplicate ID error: ' + page['path'])
        if not page.get('art_bible') or len(page.get('sections', [])) < 3:
            errors.append('Incomplete page record: ' + page['path'])
        for section in page['sections']:
            for figure in section.get('figures', []):
                if figure.get('asset') not in assets:
                    errors.append('Unknown reference in page: ' + page['path'])
    for path, parser in parsed.items():
        for link, resource in [(x, False) for x in parser.links] + [(x, True) for x in parser.resources]:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc:
                if resource:
                    errors.append('External runtime resource: ' + link)
                continue
            target = (path.parent / unquote(parts.path)).resolve() if parts.path else path
            if not link or link == '#' or not target.is_relative_to(root.resolve()):
                errors.append('Invalid relative path: ' + link)
                continue
            if not target.exists() and str(target.relative_to(root.resolve())) not in known:
                errors.append(f'{path.name}: missing target {link}')
            if target in parsed and parts.fragment not in parsed[target].ids and parts.fragment:
                errors.append('Missing fragment: ' + link)
    allowed_colors = {tuple(c['rgb']) for c in palette['colors']}
    for a in records:
        if a.get('status') not in STATUSES or not all(a.get(k) for k in ['source', 'attribution', 'rules', 'palette', 'sha256', 'source_sha256']):
            errors.append('Missing or invalid reference metadata: ' + a['id'])
        if a.get('status', '').startswith('Approved') and not a.get('owner_approval'):
            errors.append('Reference approval has no owner record: ' + a['id'])
        if a.get('palette') != palette['id']:
            errors.append('Unknown reference palette: ' + a['id'])
        path = root / a['path']
        source = root / a['source']
        if not path.is_file() or not source.is_file():
            errors.append('Missing source/export: ' + a['id'])
            continue
        try:
            image = read_png(path.read_bytes())
            if a['status'] == 'Proposed reference':
                opaque_colors = {tuple(image.pixels[i:i + 3]) for i in range(0, len(image.pixels), 4) if image.pixels[i + 3]}
                if not opaque_colors <= allowed_colors:
                    errors.append('Palette contamination: ' + a['id'])
            if [image.width, image.height] != a['dimensions']:
                errors.append('Image dimensions mismatch: ' + a['id'])
            if a.get('frame_size'):
                w, h = a['frame_size']
                if image.width % w or image.height % h or image.width // w * (image.height // h) != a['frame_count']:
                    errors.append('Invalid frame layout: ' + a['id'])
        except (ValueError, zlib.error, struct.error) as e:
            errors.append('Invalid PNG ' + a['id'] + ': ' + str(e))
        if hashlib.sha256(path.read_bytes()).hexdigest() != a['sha256']:
            errors.append('Export hash mismatch: ' + a['id'])
        if hashlib.sha256(source.read_bytes()).hexdigest() != a['source_sha256']:
            errors.append('Source/export mismatch: ' + a['id'])
    required_masks = []
    for mask in range(256):
        if all(not mask & diagonal or (mask & a and mask & b) for diagonal, a, b in [(2,1,4),(8,4,16),(32,16,64),(128,64,1)]):
            required_masks.append(mask)
    transition = assets.get('transitions', {})
    if transition.get('masks') != required_masks or len(transition.get('cells', {})) != 470:
        errors.append('Incomplete transition pattern set')
    template_paths = []
    for template in manifest['templates']:
        path = root / template['path']
        template_paths.append(template['path'])
        try:
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != template['sha256']:
                errors.append('Template hash mismatch: ' + template['path'])
            inspect_aseprite(data)
        except (OSError, ValueError, struct.error, zlib.error) as e:
            errors.append('Invalid Aseprite template ' + template['path'] + ': ' + str(e))
    allowed_binary = {a['path'] for a in records} | set(template_paths)
    for path in (root / 'art-style').rglob('*'):
        if path.suffix.lower() in {'.png', '.aseprite', '.ase', '.jpg', '.zip'} and str(path.relative_to(root)) not in allowed_binary:
            errors.append('Unregistered binary: ' + str(path.relative_to(root)))
    try:
        source = inspect_aseprite((root / 'art-style/templates/character-study.aseprite').read_bytes())
        metadata = json.loads((root / 'art-style/assets/character-walk.json').read_text())
        image = read_png((root / 'art-style/assets/character-walk.png').read_bytes())
        if len(metadata['frames']) != len(source['frames']) or source['dimensions'] != [64, 64]:
            errors.append('Source/export frame count mismatch')
        for i, frame in enumerate(metadata['frames']):
            rect = frame['frame']
            if rect != {'x': i % 6 * 64, 'y': i // 6 * 64, 'w': 64, 'h': 64} or frame['duration'] != source['durations'][i] or frame['trimmed'] or frame['rotated']:
                errors.append('Incorrect frame metadata: ' + str(i))
                continue
            pixels = bytearray(64 * 64 * 4)
            for cel in source['frames'][i].values():
                for p in range(0, len(cel), 4):
                    if cel[p + 3]:
                        pixels[p:p + 4] = cel[p:p + 4]
            if image.crop(rect['x'], rect['y'], 64, 64).pixels != pixels:
                errors.append('Source/export pixels differ: frame ' + str(i))
        if source['tags'] != [{k: t[k] for k in ['name','from','to']} for t in metadata['meta']['frameTags']]:
            errors.append('Source/export tag mismatch')
        handoff = json.loads((root / 'art-style/templates/completed-character-handoff.json').read_text())
        if handoff['source_sha256'] != hashlib.sha256((root / handoff['source_file_location']).read_bytes()).hexdigest():
            errors.append('Completed handoff source mismatch')
    except (OSError, ValueError, KeyError, IndexError, struct.error, zlib.error) as e:
        errors.append('Invalid animation association: ' + str(e))
    for path in [root / 'site/art-bible.js', root / 'site/art-bible.css']:
        text = path.read_text()
        if re.search(r'\bfetch\s*\(|@import\b|https?://', text):
            errors.append('External/offline dependency in ' + path.name)
    if check_generated:
        from create_art_references import build_outputs
        for path, data in build_outputs().items():
            if not (root / path).exists() or (root / path).read_bytes() != data:
                errors.append('Generated reference drift: ' + path)
        import build_manual_indexes
        old_root = build_manual_indexes.ROOT
        try:
            build_manual_indexes.ROOT = root
            for path, text in build_manual_indexes.build_outputs(art_only=True).items():
                if not (root / path).exists() or (root / path).read_text() != text:
                    errors.append('Generated HTML drift: ' + path)
        finally:
            build_manual_indexes.ROOT = old_root
    return {'status': 'fail' if errors else 'pass', 'scope': 'Art Bible static sources and original exports; existing-tree link references only' if reference_tree else 'Art Bible static sources and original exports in full manual', 'pages': len(pages), 'reference_pngs': len(records), 'aseprite_templates': len(template_paths), 'palette_colors': len(palette['colors']), 'transition_patterns': len(required_masks), 'errors': errors, 'engine_integration': 'not_run', 'aseprite_application_open_export': 'blocked_startup_exit_134', 'owner_art_approval': 'pending'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-tree', type=Path, help='Validate existing-manual links against a read-only GitHub tree in a focused workspace; does not prove their content.')
    args = parser.parse_args()
    report = validate(reference_tree=args.reference_tree)
    output = ROOT / 'verification/art-bible-validation.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return bool(report['errors'])


if __name__ == '__main__':
    raise SystemExit(main())
