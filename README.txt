BRIARWAKE — UNREAL ENGINE 5 C++ GAMEPLAY AND ENGINEERING REFERENCE

PROJECT BASELINE
Briarwake is a new MMORPG designed for Unreal Engine 5, native C++ and
server-authoritative dedicated servers. Game implementation is 0% complete.
Every implementation epic and ticket is Not Started with no verified runtime
evidence. No gameplay system, server, build pipeline, renderer, character, map,
database or operations infrastructure is implemented or verified. Completed
contracts and passing documentation checks are design work only.

This is the only repository needed for this documentation. The future game
implementation location is unspecified and will be established separately.
Do not create an Unreal project here or require a game checkout to build or
validate the reference. Native Unreal setup is future work described in
guide/unreal-cpp.html, not runnable game setup in this repository.

READ OFFLINE
Keep the complete directory structure and open index.html in a browser. All
reading content, styles and search records are local; no login, build or CDN is
needed to read. JavaScript enables full-site search (Ctrl/Cmd+K), table filters
and responsive navigation; content and links remain readable without it.
External references require internet. Extract ZIP packages before opening.

Use Development Roadmap for the dashboard, phases, epics, tickets, milestones,
sequence decisions, coverage and audit. Use Data Inventory for canonical enums,
interfaces, schemas and source relationships. Class/profession pages and full
catalogs remain accessible from the sidebar. Existing styles, print behavior,
responsive tables and stable anchors are preserved.

TECHNICAL FOUNDATION
C++ owns authoritative gameplay rules and state commits. Actors/components,
Pawns/Characters/controllers and framework state classes are candidate owners
according to actual lifetime and recipient requirements. Blueprints may expose
editor assets, presentation and configuration through narrow interfaces.
Enhanced Input, Gameplay Tags, Data Assets, subsystems and automation facilities
are evaluated where needed; no speculative framework or backend is mandated.

The owner already acquired the intended replication plugins. BW-100 verifies
identities, versions, license/distribution, UE/platform/source/binary constraints,
dedicated-server build/load, synchronization/serialization/relevancy, native
replication/movement interaction, security limitations and deployment/conflicts
before dependent networking work. No plugin installation or integration is
complete. Do not invent product details, buy replacements or presume persistence,
authentication, scaling or gameplay authority from replication support.

Rendering uses real-time 3D meshes, Unreal materials and post-processing, an
angled orthographic pixel-stable camera, readable silhouettes and independently
scaled UI. BW-097 verifies the fresh camera/material/pass/appearance/performance
baseline; BW-098/BW-099 cover art production and environment integration.
The concept image and selected visual references are appearance inputs only.

DESIGN PRESERVATION
Established races/factions, classes/specifications, progression/talents,
combat/status/summon rules, PvP/PvE, equipment/inventory, professions/crafting,
trade/economy, NPC/quests/world, UI/accessibility, authority/security/persistence
and engine-independent contracts remain the gameplay specification. Prototype
numbers and content readiness flags remain proposals, not balance certification.
Manifest counts are generated in data/manifest.json; do not maintain progress
or package totals independently in this README.

ROADMAP AND PROGRESS OWNERSHIP
sources/development-roadmap.json is the sole editable registry. Stable BW IDs
and criterion anchors identify responsibilities, not numeric priority. Hard
prerequisites gate execution/completion; recommended predecessors express useful
ordering. Every retained epic/ticket is Not Started with empty verified_evidence
and no carried completion claims. Milestone/phase status and dashboards derive
from records and transitive prerequisites. All later gameplay families and
separate full-game/production gates remain represented.

Tickets define scope, exclusions, exact parent criteria, dependencies, objective
checks and future setup/action/result/reset procedures. Exact native commands
are established only once the actual UE revision and target environment exist;
no nonexistent script is presented as already runnable. Later bounded epics can
be split when their prerequisites make detailed implementation planning useful.
Planning and fixture specifications never advance implementation status.

Future status updates use exactly Not Started, In Progress, Blocked or Complete.
Ordinary future dependencies are not blockers. Complete requires actual passing
evidence for every criterion on compatible tested revisions, no current failure
or blocker and completed prerequisites. Store revisions, actual artifact paths,
results and scope limits; never put documentation reports in gameplay evidence.

GENERATE AND VALIDATE DOCUMENTATION
Inspect scripts before running. Use Python 3.10+, Node.js 22+ and the pinned
formatter (npm ci). Python code uses the standard library. No Unreal engine,
plugin, game code, provider or database is required.

npm ci
python3 scripts/build_development_roadmap.py
python3 scripts/build_data_inventory.py --review-roadmap
python3 scripts/build_development_roadmap.py --check
python3 scripts/build_data_inventory.py --check
python3 validation/check_development_roadmap.py
python3 validation/check_data_inventory.py
python3 validation/check_foundation.py --baseline
python3 -m unittest discover -s validation -p 'test_*.py'
python3 validation/run_checks.py
npm run check:html
node validation/check_inventory_browser.mjs

For feature changes, review the related canonical graph first and use repeated
--review-page guide/example.html options to record the reviewed content and
regenerate its Data associations. Both builders apply pinned Prettier formatting.
npm run format:html formats published HTML; it is not a game build.

The full validator rewrites validation/report.json and the deterministic sample
allocations. The browser checker uses installed Chrome/Chromium with an isolated
temporary profile, offline file URLs, mobile/desktop, search/navigation, print
and JavaScript-disabled checks. Set BRIARWAKE_CHROME_BIN if needed. Actual browser
results are in validation/data-inventory-browser-checks.json. No runtime game
evidence is retained or credited. check_foundation.py --baseline checks the
zero-progress snapshot; its normal mode permits future evidenced development.

The tracked site is published through the repository's existing GitHub Pages
configuration. Generated HTML/assets are the deployable site; this task changes
no hosting setting and performs no deployment. There is no checked-in release
pipeline or game build. Successful documentation checks do not verify an external
Pages deployment or an Unreal build.

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

Briarwake is the implementation target. This phase writes documentation and
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
Python commands require Python 3.10+; HTML generation and generated-output
checks also require Node.js 22+ and npm ci for the pinned formatter.
The browser check uses Node 22+ and installed Chrome/Chromium without downloads.
Set BRIARWAKE_CHROME_BIN if needed. Its evidence is stored separately from the
current documentation/browser record in validation/data-inventory-browser-checks.json.

The builder owns guide/data-inventory.html, marked Data blocks, Data contents
links, the Data Inventory and Development Roadmap sidebar links, inventory- and
roadmap-tagged search records,
documentation counts in data/manifest.json, the schema bundle and the generated
review report. It preserves feature mechanics and regenerates feature-section search from current HTML.
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
