MMORPG GAMEPLAY REFERENCE — VERSION 2.3
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
214 HTML pages: 37 system/catalog/planning chapters, 97 individual epic pages,
48 ticket pages (19 foundation tickets plus 29 first-multiplayer-milestone tickets),
12 class pages, 16 profession pages, 3 full catalogs, and the main index.
Versioned JSON: 330 named abilities, 1,764 character talent nodes,
37 specialization playstyle contracts, 11 races / 12 faction-race selections,
16 professions, 240 profession mastery nodes, 257 representative recipes,
55 material definitions, 63 numerical execution profiles and 98 sample allocations.

MAIN CHANGES
World of Warcraft-style character creation and a guided level 1–10 beginner area.
The opening journey is also the first complete playable testing ground.
See guide/character-creation.html for the player-facing feature flow.
The visual target is low-resolution 3D pixel art with a character-following,
angled orthographic overview that scrolls into a close third-person perspective.
Holding middle mouse and dragging orbits the camera around the character.
David Holland and t3ssel8r are supplementary visual references, not camera
implementation specifications. The art direction in guide/decisions.html and
the rendering/camera and acceptance-test sections define project requirements. Continuous planar/floor gameplay contracts and existing
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
BW-001-T08 records completed native client/server bootstrap verification for the
pinned macOS ARM64 Development matrix. Gameplay fixtures, production database, economy,
connected Steam sessions and capacity remain unverified.

VALIDATION
The authoritative workflow is docs/validation.md.
Routine local work: python3 validation/validate.py
Focused PR gate: python3 validation/validate.py --gate
Explicit browser integration when needed: python3 validation/validate.py --mode integration --gate
Intentional comprehensive regression: python3 validation/validate.py --mode full
Unknown scope never escalates automatically. Documentation checks never execute game behavior.

HTML FORMATTING
Format manually changed HTML only with npx --no-install prettier --write PATH.
The generators format their outputs and write only changed files. PR freshness
checks do not repeat a whole-site formatter pass; FULL retains npm run format:check.
See docs/validation.md for prerequisites, source review, manual QA and evidence retention.

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
Epics begin Not Started. Live status changes require retained, scoped execution
evidence from the separately versioned game implementation.

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
The native evidence summaries below describe their recorded revisions and stage
counts, not current commands or current local plugin compatibility. Current policy
is docs/validation.md and the companion game validation policy.
BW-003 retains five native Unreal fixture tickets, BW-003-T01 through T05:
attributable evidence, deterministic context/control isolation, redacted
diagnostics, bounded measurements and integrated verification. T01 is ready
after completed BW-001/BW-002; T03 and T04 can follow T02 independently, then
T05 verifies all four epic criteria. The refreshed plan reuses the current
admission/report owners and seven native tests, preserves canonical actual
findings versus execution-failure evidence, and integrates future suites into
the existing game FULL route. T01 is Complete with 61 native checks, separate canonical execution evidence,
five stage-specific failure controls and clean recovery. At T01's recorded revision, game FULL
passed all 32 stages; 37 Python tests and the original seven-test / 3,584-content-
assertion aggregates pass. Evidence is retained under validation/tickets/BW-003-T01/.
All five BW-003 tickets are Complete. T05 joins all four existing suites in two
independent native aggregates, rejects omitted/failed/stale/foreign/partial child
evidence and preserves every prerequisite/control/package gate. At T05's recorded revision,
FULL passed all 46 supported stages and 66 Python regressions; each
aggregate passes 242 native assertions. Current evidence and the parent review
are retained under validation/tickets/BW-003-T05/. Earlier T01-T04 evidence remains
historical and applicable to their unchanged native owners.
The owner selected a local probe with logical recipients and explicitly labeled
serialized payload bytes; this does not certify connected clients or wire traffic.
BW-002 has seven tickets, T01 through T07: authority/lifecycle review, canonical
compatibility, atomic admission, unsupported-behavior rejection, owner-approved
economic contract resolution, complete economic graph admission and integrated
verification. T01 is Complete with a versioned responsibility map and retained
documentation/source review. T02 is Complete with 22-definition canonical extraction,
747 native compatibility checks, independent revision domains and failure/recovery
controls. T03 is Complete with 140 immutable fixtures and 1,284 native atomic/static
admission checks per clean/recovery run. T04 is Complete with 74 native readiness
cases / 756 checks, private earned gate evidence and normal-package isolation.
T05 is Complete with owner-selected 2.3.0-design contracts for explicit
material/item mapping, actual per-unit consumption lineage and route declarations.
T06 is Complete with 63 complete-graph fixtures and 797 native economic checks,
including combined-route gain, actual per-unit salvage, missing input, overflow,
analysis limits and atomic publication. T07 is Complete: two seven-test native
aggregates each pass all 3,584 content assertions, all 25 recorded FULL stages passed,
and report/build/failure/recovery plus normal Game/Server package isolation are
verified. Evidence is retained under validation/tickets/BW-002-T06/. Production
prices, economic mutation, persistence and connected gameplay remain unimplemented.
BW-001-T08 tracks the native bootstrap without reusing retired legacy ticket IDs.
The owner selected evanmcpheron/BriarwakeUnreal; its task branch includes the supplied
engineering docs and MultiplayerSessions Steam plugin. Actual Editor/Game builds,
native configuration/execution tests, menu Blueprint compilation, packaged-client
launch, decoded-Pak inspection and clean pass/failure/recovery controls are retained.
BW-001/T08 are Complete: the final source Server package runs headlessly outside
the source tree, checks three ticks and rejects missing/invalid configuration.
Exact artifact/source identities, clean execution controls and limitations are in
validation/tickets/BW-001-T08/final/review.json. BW-002 is Complete after its own
five-criterion review: authority/lifecycle boundaries (AC1), static admission
(AC2), unsupported-behavior/readiness (AC3), compatibility (AC4) and complete
economic graph admission (AC5). All seven tickets and integrated verification are
Complete at the recorded native source identity. Previous dated evidence under
validation/tickets/BW-002-T01/ through BW-002-T05/ remains historical; current
review, exact build/runtime/control/package artifacts and limitations are under
validation/tickets/BW-002-T06/. This certifies content admission, with no production
gameplay handler or transactional economic authority. BW-003 is Complete after its own four-criterion review and all five tickets.
Current native aggregates, controls, replay comparison, package isolation and
BW-001/BW-002 regressions pass at the recorded source/toolchain identity. This
certifies only the approved finite local probe, logical recipients and serialized
payload bytes; connected peers, production gameplay, durability and capacity
remain independent future work.
The generated ready list now contains BW-097, BW-095, BW-018, BW-004, BW-005 and
BW-006; BW-003 leaves it. BW-097/BW-095 remain Not Started, while BW-012 still has
unmet action-system prerequisites. Overall progress is 3/97 epics (3.1%).
Foundations are 3/6 complete (50%); foundations and all milestones remain
In Progress. Generated views own readiness/progress calculations.

For epic splitting, follow docs/validation.md and the focused reuse guidance at
guide/roadmap-maintenance.html. Read affected owners/contracts once and map ACs
to the smallest additional outcomes; no separate capability or ancestor audit.
The dated capability assessment and multiplayer coverage matrix on that page
record the 22 October 2026 review; recheck affected inputs before relying on it.
BW-004 through BW-013, BW-028 and BW-083 now have 29 focused planning tickets;
all begin Not Started. No gameplay progress or parent criteria changed. BW-003
T02 through T05 received targeted reuse corrections; completed tickets and
evidence are preserved. Native builds/Steam/peer/workload checks remain future
completion evidence, outside ordinary documentation generation.

BW-097 has six Not Started camera-reference tickets, T01 through T06: a native
reference scene and Unreal UI tuning, reversible follow/zoom, held middle-mouse
orbit, representative readability and independently scaled UI, authorized
floor-safe picking, and reproducible visual/performance evidence. T04 and T05
can follow T03 independently; T06 joins their evidence. Scene/control/package
paths remain planned and unverified. BW-097 remains Dependency-ready after
completed BW-001/BW-003; live gameplay systems and BW-098/BW-099 remain separate.

Store tickets in the registry's tickets list with stable IDs, parent_epic,
exact epic_criteria anchors, dependencies, scope, out_of_scope, observable
acceptance_criteria, manual_test, completion_evidence, related_docs, blockers
and verified_evidence. New tickets begin Not Started with no verified evidence.
Manual tests require launch, setup, actions, expected_results and reset, or an
explicit not_applicable rationale. Their future commands/fixtures are ticket
deliverables, not executed evidence. Ticket planning never completes an epic.
Do not edit the generated pages or search records. Rebuild and validate with:
python3 scripts/build_development_roadmap.py
python3 validation/validate.py --gate

Run the focused --gate command for final PR verification; follow docs/validation.md for additional risk-based checks.

The roadmap builder owns its HTML, search records and manifest counts. It writes
only changed files; generated pages need no inventory review fingerprints or
second generator. Status/progress views derive from the source. See docs/validation.md.

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

The 2.3.0-design economic review preserves existing identifiers/encodings and
prototype payloads. EconomicMaterialPolicy supplies the one-to-one material/item
mapping and explicit common/rare/earned and export-restriction metadata.
CraftMaterialProvenance preserves actual consumed quantities and per-unit shares
in durable lineage; salvage rounds each material down for each output unit.
EconomicRoutePolicy declares guaranteed/repeatable behavior without certifying
admission. Legacy optional absence remains readable but disables affected routes;
new content requires capability/version review. No production values or historical
provenance are inferred. See guide/items.html#economic-contracts-2-3 and the
owner decision record under validation/tickets/BW-002-T05/.

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
Iterative checks: python3 validation/validate.py --mode quick
Intentional comprehensive regression: python3 validation/validate.py --mode full
Python requires version 3.10+ and the standard library only; generated HTML uses
the local Prettier installed by npm ci through Node 22+.
The browser check uses Node 22+ and installed Chrome/Chromium without downloads.
Set BRIARWAKE_CHROME_BIN if needed. Use --report-dir to retain fresh evidence
separately from historical rendering-only and inventory browser records.

The builder owns guide/data-inventory.html, marked Data blocks, Data contents
links, the Data Inventory and Development Roadmap sidebar links, inventory search
records (preserving current roadmap records),
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
Sample bindings with catalog_scope can see shipped identities and their own named
fixture scope; shipped bindings cannot resolve references through fixture IDs.
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
The owner-selected native C++ implementation is evanmcpheron/BriarwakeUnreal,
with its pinned engine/compiler/target matrix and executed BW-001 evidence.
Reverify the actual Git root and current revision before later implementation.
The supplied MultiplayerSessions Steam plugin is included in the game repository
and has compile/widget evidence. Its connected-session, provider and replication
capabilities require separate verification; the documentation installs no plugin.
An implementation ticket cannot be executed, tested, or marked Complete until a real game repository and reproducible runtime evidence exist.

CROSS-REPOSITORY VALIDATION
The workspace game checkout owns skills/execute-ticket and skills/split-epic.
Follow docs/validation.md after explicit source review/generation. Reuse applicable
unchanged game evidence; status updates require no extra Unreal execution.
CI runs focused source/output verification on PRs, and FULL on explicit or weekly
runs. UI/template changes select browser verification. Native Unreal evidence
belongs on the pinned game host; Python/documentation CI cannot supply it.
