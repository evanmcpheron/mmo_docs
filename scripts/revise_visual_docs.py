"""One-time, scoped revision of the visual requirements and related documentation."""
from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one exact match, got {count}")
    return text.replace(old, new, 1)


def replace_section(path: str, heading_id: str, section: str) -> None:
    current = read(path)
    expression = re.compile(
        rf'<h2 id="{re.escape(heading_id)}">.*?</h2>.*?(?=<h2\b)',
        re.DOTALL,
    )
    updated, count = expression.subn(lambda _: section.rstrip() + "\n", current)
    if count != 1:
        raise AssertionError(f"{path}#{heading_id}: expected one section, got {count}")
    write(path, updated)


replace_section(
    "guide/decisions.html",
    "art-direction",
    """<h2 id="art-direction">Art direction</h2>
<p>Use real-time low-resolution 3D models with an angled orthographic camera. Favor readable character silhouettes, consistent art proportions, clear terrain and equipment, and cohesive foliage, water and lighting. <a href="https://www.davidhol.land/articles/3d-pixel-art-rendering/">David Holland’s 3D Pixel Art Rendering</a> is a visual reference, not an implementation template or technical requirement for Briarwake.</p>
<p>The <a href="https://www.youtube.com/channel/UCIjUIjWig0r5DIixQrt6A3A">t3ssel8r channel</a> and <a href="https://www.youtube.com/watch?v=ERA7-I5nPAU">Creating a Scene for my 3D Pixel Art Game</a> are supplementary visual references. Use reference comparisons during future asset reviews without prescribing a rendering technique. No game visual evidence exists yet.</p>
<p><strong>Project acceptance criteria:</strong> Review angled orthographic framing, asset proportions, color and value consistency, character/equipment readability, and camera-to-world targeting in a future Unreal Engine 5 reference scene. Compare skeletal meshes, equipment and alternate forms in motion on declared target hardware. Document supported window sizes, accessibility and visual performance evidence before scaling art production. <a href="interface.html#rendering-and-camera">Camera requirements</a> and <a href="testing.html#rendering-verification">visual verification</a> govern gameplay readability.</p>
<p>3D presentation leaves the existing continuous planar movement, floor identities, server-owned foot anchors, collision, line of sight and aim contracts unchanged. Convert those coordinates to scene transforms in the client. <code>SpriteDirection</code> keeps its existing name and eight serialized values as preview heading presets; it does not require sprite sheets or constrain animated models to eight headings. A rendering choice adds no wire fields, vertical-combat rules or new world-coordinate schema.</p>""",
)

replace_section(
    "guide/interface.html",
    "rendering-and-camera",
    """<h2 id="rendering-and-camera">Rendering and camera</h2>
<p>Apply the <a href="decisions.html#art-direction">3D pixel-art direction</a> consistently across world and character previews. Test Unreal orthographic projection, angled framing, aspect ratio, supported window sizes and zoom. Keep UI labels and pointer handling independently scalable and readable. See <a href="sources.html#s12">orthographic cameras</a> and <a href="sources.html#s13">display scaling guidance</a>.</p>
<p>Map pointer input through the displayed world content rectangle, rejecting letterbox space and UI-captured input. Account for viewport scaling and camera projection when resolving the declared gameplay floor. Ground-target previews and submitted aim must agree during camera movement, resizing and zoom. Camera presentation must never modify authoritative movement, collision or aim.</p>
<p>Keep players, selected targets and required telegraphs identifiable when roofs, walls, foliage or terrain occlude them. Presentation aids and target markers may show only server-authorized state; camera changes never expand the information envelope. Water, shadows, weather and overlapping effects must not conceal actionable hazards. Quality settings may reduce cosmetic cost while retaining required hazards, target feedback and readable contrast.</p>
<p>Pin the Unreal Engine 5 C++ toolchain and record supported camera, display and quality settings. Review representative characters, environments, lighting and water on target hardware for gameplay readability, accessible UI and measured performance. See <a href="sources.html#s10">general display quality options</a> and <a href="sources.html#s14">surface materials</a>.</p>""",
)

replace_section(
    "guide/testing.html",
    "rendering-verification",
    """<h2 id="rendering-verification">Camera and visual-readability verification</h2>
<p>Once the separate game repository exists, run native C++ client/server build tests, a standalone headless dedicated server, two-client connection and owner-only replication checks, Unreal automated/functional tests and packet-impairment recovery tests. Record executed commands, artifact revisions, observed results and failures; written scenarios do not count as passes. See <a href="sources.html#s6">dedicated server setup</a> and <a href="https://dev.epicgames.com/documentation/en-us/unreal-engine/automation-test-framework-in-unreal-engine">Unreal automation tests</a>.</p>
<p>These are future <strong>Unreal Engine 5 C++ project</strong> visual and camera tests, not website/browser validation. Record a pinned engine, built/cooked reference level, target hardware, camera/display settings and still/motion captures. No game reference scene has been executed yet.</p>
<ul>
<li>Follow a moving character and exercise each supported window size, aspect ratio and zoom setting. Check camera continuity, readable silhouettes, independently scaled text and character-preview parity.</li>
<li>Review representative characters, equipment and alternate forms across angles, distance, bright/dark scenes and animation. Target markers and actionable hazards must remain identifiable without relying only on color.</li>
<li>Verify entity selection and ground-cast markers against known server floor anchors during movement, resizing, letterboxing and zoom. Wrong-floor and letterbox input must not produce an unintended cast.</li>
<li>Review foliage, transparent objects, water, weather, particles and atmosphere together. Verify occlusion, visual clarity and server-authorized information boundaries in representative scenes.</li>
<li>Test 30-player combat with legal summon counts, overlapping hazards, dark scenes and every supported quality tier. Required telegraphs and selected-target feedback remain identifiable, including with reduced effects and accessibility settings.</li>
<li>Record CPU/GPU frame-time percentiles and memory on declared target hardware and resolutions. Measure foliage, water, atmospheric presentation and crowded combat separately against explicit budgets; retain failed results and their mitigations.</li>
</ul>""",
)

sources = read("guide/sources.html")
for identifier in ("s11", "s15"):
    expression = re.compile(
        rf'<tr>\s*<td><span id="{identifier}">.*?</tr>\s*',
        re.DOTALL,
    )
    sources, count = expression.subn("", sources)
    if count != 1:
        raise AssertionError(f"guide/sources.html#{identifier}: expected one source row, got {count}")
sources = replace_once(
    sources,
    "User-selected visual reference; camera, outlines, lighting, foliage, water and atmosphere.",
    "User-selected visual reference; framing, art consistency, lighting, foliage, water and atmosphere.",
    "source s9",
)
sources = replace_once(
    sources,
    "Renderer and upscaling choices to validate against crisp pixels",
    "General display quality and performance options",
    "source s10",
)
sources = replace_once(
    sources,
    "Internal resolution, display scaling and separate UI readability",
    "Display scaling and independently readable UI",
    "source s13",
)
sources = replace_once(
    sources,
    "select and annotate relevant clips during rendering/art work, and verify adopted techniques against the future pinned Unreal Engine 5 build.",
    "select relevant comparisons during future art reviews without prescribing a rendering technique.",
    "source s16",
)
write("guide/sources.html", sources)

readme = read("README.txt")
readme = replace_once(
    readme,
    "Roystan’s outline tutorial\n"
    "and the t3ssel8r channel supplement that reference.",
    "The t3ssel8r channel supplies supplementary art-direction references.",
    "README art sources",
)
readme = replace_once(
    readme,
    "Unreal Engine 5 version, toolchain, rendering path and plugin compatibility require prototype\n"
    "evidence before full asset production.",
    "Unreal Engine 5 version, toolchain, camera/display settings and plugin compatibility require\n"
    "verified evidence before full asset production.",
    "README technical readiness",
)
readme = replace_once(
    readme,
    "three subsequent rendering and art-production epics",
    "three subsequent camera and art-production epics",
    "README roadmap description",
)
write("README.txt", readme)

audit = read("sources/roadmap-audit.html.inc")
audit = replace_once(
    audit,
    "Unreal runtime, shader, network, persistence or capacity test",
    "Unreal runtime, network, persistence or capacity test",
    "roadmap audit evidence",
)
write("sources/roadmap-audit.html.inc", audit)

path = "sources/development-roadmap.json"
roadmap = json.loads(read(path))
roadmap["reading_guide"] = [
    sentence.replace(
        "Rendering feasibility and production work have their own evidence gates",
        "Camera/readability and art-production work have their own evidence gates",
    )
    for sentence in roadmap["reading_guide"]
]
phases = {phase["id"]: phase for phase in roadmap["phases"]}
phases["phase-foundations"]["objective"] = (
    "Establish reproducible runtime evidence, a versioned content-production route and durable ownership independently of combat. "
    "Verify orthographic camera framing and initial visual readability alongside headless development."
)
phases["phase-foundations"]["completion_condition"] = (
    "The durable retry/crash probe is executed against a real candidate store. The author/import route produces a reproducible "
    "reviewed package and rejects invalid content. A reproducible 3D reference scene verifies camera projection, target readability "
    "and initial visual/performance settings."
)
phases["phase-full-experiences"]["completion_condition"] = (
    "All-roster, progression, economic, group/PvP and usability certification pass; BW-092 separately verifies their "
    "release-candidate integration. Complete environment art and accessibility evidence are included."
)

epics = {epic["id"]: epic for epic in roadmap["epics"]}
feasibility = epics["BW-097"]
feasibility["title"] = "Orthographic camera and visual-readability proof"
feasibility["objective"] = (
    "Verify angled orthographic framing, usable camera-to-world input and the selected 3D art direction "
    "in a small future Unreal Engine 5 reference scene before scaling art production."
)
feasibility["scope"] = (
    "A reproducible Unreal Engine 5 native C++ 3D reference scene with angled orthographic framing, "
    "camera movement, representative character/environment assets, world picking, readable independent UI "
    "and baseline visual-performance checks. Full art production follows separately."
)
feasibility["acceptance_criteria"] = [
    "A reproducible Unreal Engine 5 native C++ reference scene records the tested engine/toolchain, camera configuration, target hardware and supported display settings; no previous game implementation is assumed.",
    "Angled orthographic framing, zoom and aspect/window policies keep the playable floor, characters and separately scaled UI readable across supported window sizes and high-DPI displays.",
    "Stationary, following and diagonally moving camera tests show continuous motion, readable characters and stable ground-target previews without changing authoritative movement or aim.",
    "Representative models, equipment and terrain are reviewed at gameplay distances for consistent art proportions, legible silhouettes, clear target markers and hazards in bright and dark scenes.",
    "Camera movement, zoom, resizing, occluding geometry and layered-floor views preserve valid world picking and targeting; hidden and cross-floor entities are never disclosed through the view.",
    "Versioned reference scenes reproduce on declared target configurations; still/motion captures document readability and accessibility findings, CPU/GPU frame cost, memory and supported-quality decisions.",
]
feasibility["completion_evidence"] = (
    "Versioned reference scene and camera/display settings, representative visual comparisons, "
    "world-picking and readability test evidence, captured motion and measured performance. "
    "No finished game renderer or production asset library is implied."
)
feasibility["ordering_rationale"] = (
    "Verify orthographic framing, display behavior and camera-to-world input early while server "
    "development remains independent. Do not prescribe a specialized rendering technique."
)
feasibility["related_docs"] = [
    reference for reference in feasibility["related_docs"]
    if reference["href"] != "guide/sources.html#s15"
]

interest = epics["BW-013"]
interest["acceptance_criteria"][0] = (
    "Hidden and cross-floor entities are absent from unauthorized snapshots, targeting queries "
    "and public correlation identifiers; client presentation and selection cannot reconstruct "
    "or reveal excluded entities."
)
movement = epics["BW-005"]
movement["acceptance_criteria"][1] = (
    "Independent aim and motion remain continuous regardless of model facing, eight preview headings, "
    "camera projection or other visual presentation choices."
)
controls = epics["BW-028"]
controls["acceptance_criteria"][3] = (
    "Keyboard bindings, text/UI scale and reduced visual effects can be exercised independently "
    "of world display settings; model poses and camera presentation never determine aim, collision or release."
)
controls["acceptance_criteria"][4] = (
    "Pointer ground previews and selection map through actual viewport scaling, letterbox offsets "
    "and camera projection to the intended server floor/position; UI capture and invalid/occluded "
    "geometry have deterministic rejection/cancel behavior."
)

environment = epics["BW-099"]
environment["scope"] = (
    "Terrain, foliage, water, lighting, weather/ambient art and supported visual-quality tiers. "
    "These are presentation requirements, not new weather, swimming or day/night gameplay systems."
)
environment["acceptance_criteria"][1] = (
    "Water and shoreline scenes retain legible characters, terrain boundaries, selection and "
    "relevant hazards across supported views and quality tiers; visual presentation never reveals hidden state."
)
environment["acceptance_criteria"][2] = (
    "Atmospheric light, rain, dust and ambient effects remain visually consistent without masking "
    "targets or critical telegraphs; supported quality tiers preserve gameplay clarity and have measured costs."
)
environment["acceptance_criteria"][3] = (
    "Roofs, trees, water and layered floors have verified occlusion and visibility behavior; "
    "concealed or cross-floor entities are not disclosed through the scene or targeting interface."
)
environment["completion_evidence"] = (
    "Versioned environment scenes, art-direction comparisons, visibility/accessibility recordings, "
    "measured resource budgets and a tested quality/platform matrix."
)
environment["ordering_rationale"] = (
    "Build on established camera and asset conventions; full presentation and release capacity "
    "must evaluate complete gameplay environments."
)

milestones = {milestone["id"]: milestone for milestone in roadmap["milestones"]}
milestones["milestone-foundations"]["objective"] = (
    "Prove clean runtime artifacts, a versioned content-production route and one durable conflict/crash-safe "
    "mutation. Verify camera/input readability before scaling art production."
)
milestones["milestone-foundations"]["outcome"] = (
    "A clean headless fixture run and real-store concurrency/retry/crash evidence exist with explicit "
    "authority/content boundaries. Reproducible reviewed content import/export and invalid-package rejection "
    "establish the production route. A reference 3D scene verifies camera framing, selection clarity and "
    "baseline visual performance without certifying production art."
)
milestones["milestone-full-experiences"]["outcome"] = (
    "Level 1–60, voluntary PvE level sync, dungeons/raids, flagged/duel/objective PvP, "
    "professions/economy, full-state recovery and accessible presentation have certified content and "
    "recorded balance/relevance findings. Complete character and environment art passes the supported "
    "visual-quality and performance checks."
)

for item in roadmap["coverage"]:
    if item["family"].startswith("3D pixel-art renderer,"):
        item["family"] = "3D art direction, orthographic camera, asset production and environment presentation"

for decision in roadmap["sequencing_decisions"]:
    if decision["id"] != "decision-rendering":
        continue
    decision["title"] = "Camera and art foundations before asset volume"
    decision["choice"] = (
        "Verify angled orthographic framing, world picking and visual readability alongside headless "
        "development; establish repeatable art import conventions before starter production and "
        "certify complete environments and assets before release."
    )
    decision["alternatives"] = (
        "Deferring camera and artwork checks until final polish risks unusable input projection "
        "and inconsistent assets. The camera and art reviews should remain limited to observable "
        "readability, compatibility and performance rather than assuming a particular rendering technique."
    )
    decision["basis"] = (
        "The visual goal is low-resolution pixel-art-inspired 3D with an angled orthographic camera. "
        "Reference art is illustrative, not a prescribed technical implementation. "
        "Camera, asset and performance decisions do not change simulation authority, movement or wire encodings."
    )

for decision in roadmap["open_decisions"]:
    if decision["id"] != "open-rendering":
        continue
    decision["title"] = "Camera, asset conventions and supported visual quality"
    decision["description"] = (
        "Pin the tested Unreal Engine version and supported platforms, orthographic pitch/framing, "
        "zoom, aspect/minimum-window policy, model/material/animation conventions, "
        "environment presentation and client performance budgets. These choices require evidence; "
        "no fixed dimensions or special rendering technique is implied."
    )
    decision["resolution_gate"] = (
        "BW-097 verifies the camera/readability and display baseline; BW-098 establishes repeatable "
        "asset conventions; BW-099 reviews complete environments; BW-074/BW-090 approve release "
        "visual accessibility and performance across supported quality tiers."
    )

roadmap["critical_review"] = [
    (
        "Art-direction revision: replaced the former 2D sprite mandate with the selected 3D pixel-art "
        "reference. BW-097/BW-098/BW-099 cover early orthographic camera/readability verification, "
        "reusable art production and environment integration, while independent headless development "
        "and full release visual/performance checks remain required."
        if item.startswith("Art-direction revision:")
        else item
    )
    for item in roadmap["critical_review"]
]
write(path, json.dumps(roadmap, ensure_ascii=False, indent=2) + "\n")

for check_path in (
    "README.txt",
    "guide/decisions.html",
    "guide/interface.html",
    "guide/testing.html",
    "guide/sources.html",
    "sources/development-roadmap.json",
    "sources/roadmap-audit.html.inc",
):
    current = read(check_path)
    forbidden = ("shader", "hlsl", "glsl")
    if any(term in current.lower() for term in forbidden):
        raise AssertionError(f"Forbidden terminology remains in {check_path}")

print("Updated visual source documentation and retained all roadmap epic IDs.")
