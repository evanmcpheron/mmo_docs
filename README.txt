MMORPG GAMEPLAY REFERENCE — VERSION 2.2
Mechanics and architecture reference for a planned Unreal Engine 5 native C++ MMORPG

OPEN THE REFERENCE
1. Extract the entire ZIP, keeping the folder structure intact.
2. Open index.html in a desktop web browser.
3. Start with Character creation & beginner area, then Design decisions,
   Levels & talent points, and Specializations & playstyles.

All reading content, styles and search data are included locally. No account,
package installation, API key, build step or external CDN is required.
External source links require internet access. Keep assets/ beside the HTML.
Do not open index.html inside a ZIP preview without extracting the other files.

NAVIGATION
The sidebar opens Development Roadmap prominently, then groups system rules,
classes, professions and catalogs.
Search the full reference from the top bar (Ctrl+K or Cmd+K).
Catalog pages also have local table filters. Page headings have stable anchors.
Use the browser Print command or the Print button for the current page.
The documentation remains readable with JavaScript disabled; live search and
filters require JavaScript. Dense tables scroll horizontally on small screens.

PACKAGE CONTENTS
172 HTML pages: 37 system/catalog/planning chapters, 97 individual epic pages,
five individual BW-003 ticket pages and one native BW-001 execution ticket,
12 class pages, 16 profession pages, 3 full catalogs, and the main index.
Versioned JSON: 330 named abilities, 1,764 character talent nodes,
37 specialization playstyle contracts, 11 races / 12 faction-race selections,
16 professions, 240 profession mastery nodes, 257 representative recipes,
55 material definitions, 63 numerical execution profiles and 98 sample allocations.

MAIN CHANGES
World of Warcraft-style character creation and a guided level 1–10 beginner area.
The opening journey is also the first complete playable testing ground.
See guide/character-creation.html for the player-facing feature flow.
The visual target is low-resolution 3D pixel art with an angled orthographic
camera, following the user-selected David Holland article. The t3ssel8r channel supplies supplementary art-direction references. The art direction in
guide/decisions.html and the rendering/camera and acceptance-test sections define
project requirements. Continuous planar/floor gameplay contracts and existing
SpriteDirection values remain compatible; the renderer does not mandate sprites.
Unreal Engine 5 version, toolchain, camera/display settings and plugin compatibility require
verified evidence before full asset production.
Two points on each level-up from 2 through 60: 59 class + 59 specialization.
Specialization points are banked before level 10. Level 1 starts at zero.
Humans can choose either faction with identical racial attributes; Ogres removed.
Paladin/Cleric: good side only. Necromancer/Warlock: evil side only.
Other classes are shared. No fictional geography, history or cultures included.
Two manufacturing professions plus two gathering professions; Cooking, Fishing
and First Aid are available to everyone. Profession skill is independent of
character talent points. Six bands provide useful leveling output.

READINESS
Numerical coefficients, progression pacing, item budgets and recipes are
prototype proposals, not verified game balance. Named secondary ability effects
and many inherited talent behaviors still require explicit runtime binding.
Read guide/audit.html before treating this as implementation-ready game content.
The native Unreal C++ bootstrap is versioned in evanmcpheron/BriarwakeUnreal.
BW-001-T08 records actual client/build/configuration/inspection evidence; dedicated
server verification remains active. Gameplay fixtures, production database, economy,
connected Steam sessions and capacity remain unverified.

VALIDATION
Run: python validation/run_checks.py
Requires Python 3.10+; standard library only. The script rewrites report.json
and allocation_examples.json. It does not regenerate HTML or run a game.
The HTML evidence page records checks from package generation; report.json is
the source of truth after a later rerun.

validation/browser-checks.json preserves the original rendering-only evidence
and its navigation limitations. Current inventory and roadmap browser evidence is recorded
in validation/data-inventory-browser-checks.json: actual offline file navigation,
canonical definitions, filters/search, feature links, roadmap epics, mobile layout,
print visibility and reading with JavaScript disabled, using an isolated installed
Chrome profile.

DATA EDITING
HTML is a static published snapshot. Editing JSON does not automatically update
HTML tables or search data. Change matching reference pages and regenerate the
search index before distributing an edited version. Preserve stable IDs and
increment content versions when meanings change.

DEVELOPMENT ROADMAP AND PROGRESS
Open guide/development-roadmap.html for the roadmap overview, progress dashboard,
recommended sequence and actionable epics. Each phase has a separate
guide/roadmap-*.html index. Each epic has its own guide/roadmap-bw-NNN.html page
with prerequisites, downstream work, acceptance criteria, verification and ticket
planning. Criterion links such as #BW-097-AC-1 support future ticket references.
Previous/next links follow the recommended sequence, and breadcrumbs return to
the containing phase. Dedicated reference pages
cover milestones, architectural decisions, feature coverage and progress upkeep.
Use the roadmap navigation on any of these pages to move between them. Existing
overview- and phase-page epic anchors remain links to the corresponding epic pages.
It is planning/reference documentation; it adds no canonical gameplay contracts.
All epic statuses begin Not Started because this repository contains design
evidence, not verified game implementation.

Open guide/roadmap-audit.html for the independent 17 October 2026 audit of all
92 original epics, ten findings, applied corrections and the remaining rated-entry
policy decision. The corrected audit baseline had 94 epics; the current roadmap
has 97, including three subsequent camera and art-production epics (BW-097,
BW-098 and BW-099). The dated report's editable source is
sources/roadmap-audit.html.inc; the roadmap builder publishes it using
the same template/navigation and the inventory builder indexes its findings.
The report is a planning snapshot, separate from live implementation progress.

sources/development-roadmap.json is the sole editable roadmap/progress source.
Edit an existing epic's status and verified_evidence there. Use exactly Not
Started, In Progress, Blocked or Complete; record blockers for Blocked and actual
evidence for Complete. Retain IDs when reordering; assign an unused BW ID when
adding an epic, then update relevant dependencies, milestones and coverage.
BW-003 has five native Unreal fixture tickets, BW-003-T01 through T05, in
execution order: attributable evidence, deterministic context/control isolation,
redacted diagnostics, bounded measurements and integrated verification. They
cover all four epic criteria and begin Not Started with no verified evidence.
The owner selected a local probe with logical recipients and explicitly labeled
serialized payload bytes; this does not certify connected clients or wire traffic.
BW-001-T08 tracks the native bootstrap without reusing retired legacy ticket IDs.
The owner selected evanmcpheron/BriarwakeUnreal; its task branch includes the supplied
engineering docs and MultiplayerSessions Steam plugin. Actual Editor/Game builds,
native configuration/execution tests, menu Blueprint compilation, packaged-client
launch, decoded-Pak inspection and clean pass/failure/recovery controls are retained.
The source-engine Server build and remaining package/smoke checks are still active,
so BW-001/T08 remain In Progress. BW-002/BW-003 remain Not Started; BW-003 is not
Dependency-ready. See the registry and BW-001 evidence for exact scope and revisions.

Store tickets in the registry's tickets list with stable IDs, parent_epic,
exact epic_criteria anchors, dependencies, scope, out_of_scope, observable
acceptance_criteria, manual_test, completion_evidence, related_docs, blockers
and verified_evidence. New tickets begin Not Started with no verified evidence.
Manual tests require launch, setup, actions, expected_results and reset, or an
explicit not_applicable rationale. Their future commands/fixtures are ticket
deliverables, not executed evidence. Ticket planning never completes an epic.
Do not edit the generated pages or search records. Rebuild and validate with:
python3 scripts/build_development_roadmap.py
python3 scripts/build_data_inventory.py --review-roadmap
python3 scripts/build_development_roadmap.py --check
python3 scripts/build_data_inventory.py --check
python3 validation/check_development_roadmap.py
python3 validation/check_data_inventory.py
python3 -m unittest discover -s validation -p 'test_*.py'
python3 validation/run_checks.py

The roadmap builder owns the hub, phase indexes, individual epic/ticket pages and
roadmap reference pages. The
inventory builder's --review-roadmap option registers and refreshes all of these
as planning references, without adding gameplay data associations. It refreshes
navigation, direct detail-page search links, page review metadata and manifest counts.
Generated dashboards, phase progress and milestone states derive from the same
epic statuses. Every page remains readable offline and with JavaScript disabled.

DATA INVENTORY AND CANONICAL CONTRACTS
Open guide/data-inventory.html or choose Data Inventory in the Catalogs sidebar.
All 501 original structures have been examined together. Enums, Interfaces and
Schemas remain separate groups with stable original names and anchors. Fourteen
content-driven classifications now use content-reference schemas instead of
closed enums. Current totals and completion counts are generated in Coverage
and validation/data-model-review.txt; partial contracts say Needs Decision.

Every associated feature page ends with Data. A type link opens its canonical
members, properties, requiredness, nullability, relationships, constraints and
source evidence. Long definitions use native HTML disclosures that work offline
and without JavaScript. Existing table filters and global search index contracts,
fields, dependencies and feature associations.

sources/data-inventory.json is the sole editable definition registry (format 2).
It contains JSON Schema 2020-12 fragments, shared definitions, conventions,
authority/lifecycle decisions, dependency groups, source associations, coverage,
review questions and source-record validation bindings. No gameplay code is here.
The registry format version is independent of content/rules/database versions.
Its content_version owns the reviewed package revision; the generated schema
bundle exposes the same revision as x-content-version, and validation rejects
a character catalog with a different package version.

sources/data-model.schema.json is a generated language-neutral $defs bundle.
Select a named definition when validating; the bundle root is a catalog, not a
single gameplay payload. Enums with established values preserve their encodings.
x-members represents symbolic alternatives without inventing wire encodings.
Reviewed enums now use exact string encodings while preserving existing values.
Needs Decision means the schema covers only the supported portion. x-invariants
record semantic checks that a future server/content validator must enforce.
Neither a schema match nor Fully Defined certifies runtime bindings or balance.

The 2.1.0-design review resolves targeting inputs for all 21 existing modes,
nullable unused command fields, checked optional character identity and current-
session coordinate scope. New messages have versioned discriminators; existing
ability_command_v2 keeps its name. command_targeting_errors in scripts/data_model.py
checks a command against its resolved policy; session identity, visibility, range
and world geometry still require authoritative runtime checks.

Equipment uses explicit personal equipment-container placement and atomic slot,
item and container revisions. Invitations have versioned one-use lifecycles;
guild commands use exact variants and rolling committed withdrawal accounting.
Public combat results redact hidden sources and exclude internal breakdowns.
Status cleanup flags compose explicitly. Minstrel costs, deterministic Ranger
talent behavior, support accounting and the two-unit Bonewright category agree
across the canonical contracts, shipped data, feature guidance and search.

All original type names and anchors remain. ItemRarity is a compatibility alias
of ItemGrade; StatusPersistencePolicy is a composable object schema.

The 2.2.0-design documentation pass completes all 501 contracts and resolves all
29 recorded design questions. It specifies clause routes, status/cleanse policy,
finite NPC behavior, quest/loot credit, optional typed runtime bindings, naming
and appearance rules, starter relationships, economy configuration, abstract
security/operations contracts, fixture expectations and the first PvP rules.
Required content parameters remain explicit; a concrete art/map/price record is
future content production, not an unanswered question about its schema.

Briarwake targets Unreal Engine 5 native C++, with Blueprint assets used where
suitable. The dated workspace inspection above records the local starter and
remaining implementation prerequisites. This phase writes documentation and
language-neutral contracts only. The inventory preserves resolved decision
history and separately labels future Briarwake implementation work. No game
handlers, maps/art, provider/database deployment or gameplay test executions
are claimed. Shipped prototype content retains its current readiness markers.
Fixture run evidence explicitly distinguishes unexecuted specifications from
actual passed/failed execution; schema checks never promote those states.

Build: python3 scripts/build_data_inventory.py
Check without writing: python3 scripts/build_data_inventory.py --check
Focused consistency check: python3 validation/check_data_inventory.py
Regression tests: python3 -m unittest discover -s validation -p 'test_*.py'
Full existing checks, including inventory: python3 validation/run_checks.py
Optional rendered checks: node validation/check_inventory_browser.mjs
All Python commands require Python 3.10+ and the standard library only.
The browser check uses Node 22+ and installed Chrome/Chromium without downloads.
Set BRIARWAKE_CHROME_BIN if needed. Its evidence is stored separately from the
historical rendering-only record in validation/data-inventory-browser-checks.json.

The builder owns guide/data-inventory.html, marked Data blocks, Data contents
links, the Data Inventory and Development Roadmap sidebar links, inventory- and
roadmap-tagged search records,
documentation counts in data/manifest.json, the schema bundle and the generated
review report. It preserves original feature content and noninventory search.
Existing feature HTML remains authoritative for mechanics; the original full-site
generator is not included. Rebuilds are deterministic and never duplicate Data.

For a model change, read every associated mechanic and related contract first.
Edit its canonical definition in the registry, reuse local $refs and keep source
IDs/keys/encodings. Update references to match the definition graph. Distinguish
runtime, persistent, static, request, response and client-view authority. Record
inferred structural choices in modeling_notes. Required properties must occur
in required; nullability is explicit. No default exists unless documented.

Preserve feature_pages/evidence agreement and canonical_page section evidence.
reviewed_against records the evidence examined for each definition. New questions
need affected entries, source references, alternatives, recommendation, impact
and state. Link every open issue back from its affected entries and set their
definition_status to Needs Decision and definition_extent to Partial. Fully
Defined/Complete is allowed only after all attached questions are resolved.
Keep resolved question anchors with their reasoning; clear their open backlinks.

When feature text changes, review associations/definitions first, update the
per-contract evidence review, then record the completed page review and rebuild:
python3 scripts/build_data_inventory.py --review-page guide/example.html
The option is repeatable. New feature pages require supported associations;
reference/index exclusions require an explicit rationale. No arbitrary mechanics
or missing numerical balance values may be filled in merely to complete a type.

Validation detects duplicate IDs/names, undefined references, invalid schema
vocabulary, enum drift, value-containment cycles, orphan helpers, stale dependency
metadata, mismatched decision coverage, missing evidence, missing/duplicate Data,
local link/anchor problems, changed source text and generated output drift.
Every sample binding validates all selected records, including individual ability
overrides and embedded catalog copies, against the same canonical schema. Typed
content references are checked against shipped catalogs where those exist.
The focused standard-library validator supports exactly the keywords used here;
it fails on unsupported keywords rather than claiming full JSON Schema support.
It does not execute textual invariants, symbolic wire encodings or gameplay.

validation/data-model-review.txt records definition coverage, DRY changes,
ownership/dependency decisions, all outstanding questions and per-type evidence.
validation/report.json and data-inventory-browser-checks.json record actual runs.
Housing, territory, sieges, authored geography, long offline manufacturing and
other deferred mechanics remain outside the current documented model.

SOURCES
Official research links are in guide/sources.html. The source archive checksum
is in data/provenance.json. Original attached files were left unchanged.
No branding or name in this reference has received a legal clearance review.

UNREAL ENGINE 5 PROJECT BOUNDARY
This repository is the authoritative gameplay and planning reference, not the game source.
Create a separate native C++ Unreal Engine 5 project and repository in a later task; do not invent or assume its location.
Before implementation, select and pin the engine revision, supported C++ compiler/toolchain and platforms.
The owner has replication plugins available, but names, licensing, supported engine revisions and capabilities require verification before design or integration; none is installed or configured here.
An implementation ticket cannot be executed, tested, or marked Complete until a real game repository and reproducible runtime evidence exist.
