from pathlib import Path
import json
from PIL import Image

root = Path(__file__).resolve().parent
rows = []
for zoom in range(2):
    for lighting in range(3):
        prefix = f'courtyard-z{zoom}-l{lighting}-'
        source = Image.open(root / (prefix + 'pbr.png')).convert('RGB')
        toon = Image.open(root / (prefix + 'toon.png')).convert('RGB')
        count = sum(max(toon.getpixel((x, y))) <= 2 and max(source.getpixel((x, y))) > 12
                    for y in range(source.height) for x in range(source.width))
        rows.append({'zoom': zoom, 'lighting': lighting,
                     'source_visible_to_near_black_pixels': count,
                     'test': 'Source max RGB8 >12 and toon max RGB8 <=2, all pixels. A diagnostic for unexplained collapse, not visual acceptance or a replacement for masks.'})
(root / 'dark-material-collapse.json').write_text(json.dumps(rows, indent=2) + '\n')
print(json.dumps(rows))
