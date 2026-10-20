from html import escape
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2] / 'scripts'))
from build_data_inventory import navigation
from html_format import format_html_documents

review = json.loads((ROOT / 'visual-review.json').read_text())
capture_directory = review['capture_directory']
run = json.loads((ROOT / capture_directory / 'run.json').read_text())
observations = {row['label']: row for row in run['actual']['observations']}
comparison = review['presentation_comparison']
comparison_directory = comparison['capture_directory']
comparison_run = json.loads((ROOT / comparison_directory / 'run.json').read_text())
native_width, native_height = comparison_run['actual']['native_comparison']['native_size']
concept = '../../../assets/graphics_concept.png'


def crop(path, rectangle, label):
    x, y, width, height = rectangle
    return (f'<svg viewBox="{x} {y} {width} {height}" role="img" aria-label="{escape(label)}">'
            f'<image href="{path}" width="{1672 if path == concept else 384}" '
            f'height="{941 if path == concept else 216}"/></svg>')


rows = []
for region in review['comparison_regions']:
    label = region['id']
    capture_label = region['capture']
    rows.append(f'<article><h3>{escape(label.capitalize())}</h3><div class="crops"><figure>'
                + crop(concept, region['concept_rectangle'], 'Concept ' + label)
                + '<figcaption>Principal concept · native source crop</figcaption></figure><figure>'
                + crop(capture_directory + '/' + capture_label + '-internal.png', observations[capture_label]['regions'][label],
                       'Probe ' + label)
                + '<figcaption>Courtyard · projected region in the declared capture</figcaption></figure></div><p>'
                + escape(region['observation']) + '</p></article>')

annotations = ''
for index, region in enumerate(review['comparison_regions'], 1):
    x, y, width, height = region['concept_rectangle']
    annotations += (f'<rect x="{x}" y="{y}" width="{width}" height="{height}"/>'
                    f'<text x="{x}" y="{y-8}">{index} {escape(region["id"])}</text>')

bounds = ''.join(f'<tr><td>{escape(bound["id"])}</td><td>{escape(bound["bound"])}</td>'
                 f'<td>{escape(bound["status"])}</td></tr>' for bound in review['proposed_bounds'])
references = ''.join(f'<li><a href="{escape(ref["url"])}">'
                     f'{escape(ref.get("timestamp", ref.get("section", "Reference")))}</a> · '
                     f'{escape(ref["observation"])} <strong>{escape(ref["review"])}</strong>'
                     + (f' <a href="{escape(ref["capture"])}">Inspected frame</a>' if ref.get('capture') else '')
                     + '</li>'
                     for ref in review['supplementary_references'])
lighting = ''.join(f'<figure><img src="{capture_directory}/{light}-zoom-1-internal.png" '
                    f'width="384" height="216" alt="{light} lighting at native gameplay scale">'
                    f'<figcaption>{light.capitalize()} · 384×216 native pixels</figcaption></figure>'
                    for light in ('day', 'warm', 'cool'))
findings = ''.join(f'<li>{escape(finding)}</li>' for finding in review['blocking_findings'])
deviations = ''.join(f'<li>{escape(item)}</li>' for item in review['proposed_deviations'])
provenance = review['asset_provenance']
limitations = ''.join(f'<li>{escape(item)}</li>' for item in provenance['limitations'])
budget = review['proposed_budgets']
html = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BW-097-T03 · visual baseline review</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#10191e;color:#e1e5df;font:16px/1.6 system-ui,sans-serif}}
main{{max-width:1200px;margin:auto;padding:36px 32px 80px}}h1{{font-size:36px;line-height:1.2;margin:8px 0 18px}}h2{{font-size:24px;margin-top:42px}}
h3{{color:#dfbc7d}}p{{color:#c1cbc7}}a{{color:#9ed6da}}.eyebrow{{letter-spacing:.16em;color:#dfbc7d;font-size:12px;text-transform:uppercase}}
nav{{max-width:1200px;margin:auto;padding:16px 32px 0;display:flex;gap:18px;align-items:center;font-size:12px}}nav p{{margin:0}}.badge{{border:1px solid #a17b3b;color:#efd29a;padding:7px 12px;display:inline-block;border-radius:6px}}
.hero{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}figure{{margin:0;min-width:0}}img{{max-width:100%;height:auto;image-rendering:pixelated}}
.hero img{{width:100%}}figcaption{{font-size:12px;color:#aab8b0;margin-top:8px}}.hero svg{{width:100%;display:block}}
.comparison img.native-pbr,.overview img{{image-rendering:auto}}.overview img{{width:100%}}.comparison a{{display:block}}
rect{{fill:none;stroke:#f6db79;stroke-width:3}}text{{fill:#fff2a5;font:22px system-ui;paint-order:stroke;stroke:#172027;stroke-width:5px}}
.cards{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}article{{background:#19262c;padding:20px;border-radius:8px}}article h3{{margin:0 0 14px}}
.crops{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}.crops svg{{width:100%;height:190px;background:#10191e;image-rendering:pixelated}}
.native{{display:flex;flex-wrap:wrap;gap:16px}}.native figure{{width:384px}}table{{border-collapse:collapse;width:100%}}th,td{{text-align:left;vertical-align:top;border-bottom:1px solid #37464c;padding:12px}}th{{color:#dfbc7d}}
code{{font-size:12px;overflow-wrap:anywhere}}.notice{{border-left:3px solid #dfbc7d;padding:12px 18px;background:#20292b}}li{{margin-bottom:10px}}
@media(max-width:700px){{main{{padding:22px 16px}}.hero,.cards{{grid-template-columns:1fr}}h1{{font-size:28px}}.crops svg{{height:150px}}}}
@media print{{body{{background:white;color:black}}p,figcaption{{color:#333}}article,.notice{{background:#eee}}a{{color:#13435e}}}}
</style><nav aria-label="Reference navigation"><a class="nav-home" href="../../../index.html">Overview</a><p>Catalogs</p></nav><main><div class="eyebrow">Briarwake · BW-097-T03 · {escape(review['version'])} · {escape(review['date'])}</div>
<h1>Project Titan · a courtyard around the character</h1><div class="badge">{escape(review['status'])}</div>
<p>A 1.8m Adventurer stands on cobblestone paving beside a small market. Barrels, pottery, containers, produce crates and a stool provide nearby detail; the house, birch and canopy establish larger scale. Select each image to inspect its full resolution.</p>
<figure class="overview"><a href="{capture_directory}/overview-native.png"><img src="{capture_directory}/overview-native.png" width="{native_width}" height="{native_height}" alt="Project Titan courtyard overview with a complete adventurer and correctly scaled small and large scenery"></a><figcaption>Whole courtyard · native-resolution PBR · 12m orthographic height. <a href="{capture_directory}/overview-pixelated.png">Matching pixelated overview</a> · <a href="titan-placement-review.json">Measured heights and support placement</a>.</figcaption></figure>
<h2>Before and after pixel presentation</h2><p>{escape(comparison['meaning'])} {escape(comparison['state'])}. Both images have the same {native_width}×{native_height} dimensions. Select an image to inspect the full-size capture.</p>
<div class="hero comparison"><figure><a href="{comparison_directory}/{comparison['before']}"><img class="native-pbr" src="{comparison_directory}/{comparison['before']}" width="{native_width}" height="{native_height}" alt="Before: native-resolution PBR render with pixel presentation disabled"></a><figcaption>Before · native-resolution PBR · pixel presentation off</figcaption></figure>
<figure><a href="{comparison_directory}/{comparison['after']}"><img src="{comparison_directory}/{comparison['after']}" width="{native_width}" height="{native_height}" alt="After: matching scene rendered at 384 by 216 and enlarged with nearest sampling"></a><figcaption>After · 384×216 with nearest integer upscale · current prototype</figcaption></figure></div>
<p>{escape(comparison['verification'])} <a href="{comparison_directory}/run.json">Comparison execution and image hashes</a>. The high-resolution image is diagnostic; gameplay readability still needs review at 384×216.</p>
<h2>Principal concept and gameplay pixels</h2><p>The original concept remains the appearance reference. The current courtyard uses Titan assets and starts in the closer view, with a separate overview. These are comparison inputs; artistic acceptance remains pending.</p>
<div class="hero"><figure><svg viewBox="0 0 1672 941" role="img" aria-label="Principal concept with numbered comparison regions"><image href="{concept}" width="1672" height="941"/>{annotations}</svg><figcaption>Principal concept · unchanged SHA-256 <code>{review['principal_reference']['sha256']}</code></figcaption></figure><figure><img src="{capture_directory}/day-zoom-1-internal.png" width="384" height="216" alt="Titan courtyard at the closer gameplay view"><figcaption>Close view · 384×216 gameplay pixels · day / 4.5m orthographic height. Character scale remains 1.8m.</figcaption></figure></div>
<h2>Character, props, depth and lighting</h2><div class="cards">{''.join(rows)}</div>
<h2>Native gameplay pixels</h2><p>Each image below has 384×216 source pixels, displayed 1:1 when room permits. Compare character part separation and warm/cool light in the initial close view here.</p><div class="native">{lighting}</div>
<p><a href="{capture_directory}/day-zoom-1-internal.png">Close gameplay view</a> · <a href="{capture_directory}/day-zoom-1-output.png">Native Retina output with independent HUD</a> · <a href="{capture_directory}/run.json">Actual execution and capture hashes</a></p>
<h2>Imported fixture provenance</h2><p>The user-selected Project Titan library supplies the character and courtyard assets. Source and converted models/textures remain local; the recipe and rendered evidence are retained. The original Unreal project is read-only. Reproduction requires an authorized local copy of that library.</p>
<p><a href="{provenance['recipe']}">Selected asset recipe</a> · <a href="{provenance['manifest']}">Engine, source/dependency and converted hashes</a> · <a href="{provenance['export_log']}">Unreal export log</a></p><ul>{limitations}</ul>
<h2>Proposed observable bounds</h2><table><thead><tr><th>Area</th><th>Review proposal</th><th>Decision</th></tr></thead><tbody>{bounds}</tbody></table>
<h2>Provisional measurement budgets — approval required</h2><p>Proposal for this source probe on Apple M2 Max / Metal: {budget['target_fps']} FPS; CPU frame p95 ≤{budget['cpu_frame_p95_ms']:g} ms; GPU frame p95 ≤{budget['gpu_frame_p95_ms']:g} ms; peak process RSS ≤{budget['process_rss_peak_mib']:,} MiB; peak engine rendering allocations ≤{budget['rendering_allocations_peak_mib']:,} MiB. Use 384×216 internal and 960×640 logical output on actual Retina ×2. These are proposals, with no measured compliance claim. T10 must retain warmup, raw samples, percentiles and separate process/engine memory accounting; unavailable GPU timings cannot pass.</p>
<h2>Proposed deviations</h2><ul>{deviations}</ul>
<h2>Supplementary research</h2><ul>{references}</ul>
<h2>Review decision</h2><div class="notice"><strong>Reviewer: {escape(str(review['reviewer']))} · approval: {escape(str(review['approved_at']))}</strong><ul>{findings}</ul><p>Confirm or revise the visual bounds, budgets and deviations. Supplementary frames at 00:03 and 00:30 have been inspected separately; the original 00:00/04:40 proposals are superseded. Human approval establishes a comparison baseline only. Later motion/effect/package tests remain required.</p></div>
<p>Source of review decisions: <a href="visual-review.json">visual-review.json</a>. Regenerate this sheet with <code>python3 validation/tickets/BW-097-T03/build_review.py</code> from mmo_docs/. The concept remains unchanged, comparison crops use SVG view boxes, and no reference art is imported into the game.</p><footer>BW-097-T03 retained comparison evidence · acceptance decisions remain in visual-review.json.</footer></main></html>'''
relative = 'validation/tickets/BW-097-T03/review.html'
html = navigation(html, relative)
(ROOT / 'review.html').write_text(format_html_documents({relative: html})[relative])
