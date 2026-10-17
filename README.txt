MMORPG GAMEPLAY REFERENCE — VERSION 2.0
Mechanics design, not a playable Godot project

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
The sidebar groups system rules, classes, professions and catalogs.
Search the full reference from the top bar (Ctrl+K or Cmd+K).
Catalog pages also have local table filters. Page headings have stable anchors.
Use the browser Print command or the Print button for the current page.
The documentation remains readable with JavaScript disabled; live search and
filters require JavaScript. Dense tables scroll horizontally on small screens.

PACKAGE CONTENTS
54 HTML pages: 22 system/catalog chapters, 12 class pages, 16 profession pages,
3 full catalogs, and the main index.
Versioned JSON: 330 named abilities, 1,764 character talent nodes,
37 specialization playstyle contracts, 11 races / 12 faction-race selections,
16 professions, 240 profession mastery nodes, 257 representative recipes,
55 material definitions, 63 numerical execution profiles and 98 sample allocations.

MAIN CHANGES
World of Warcraft-style character creation and a guided level 1–10 beginner area.
The opening journey is also the first complete playable testing ground.
See guide/character-creation.html for the player-facing feature flow.
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
No Godot client/server, production database, economy or load test is included.

VALIDATION
Run: python validation/run_checks.py
Requires Python 3.10+; standard library only. The script rewrites report.json
and allocation_examples.json. It does not regenerate HTML or run a game.
The HTML evidence page records checks from package generation; report.json is
the source of truth after a later rerun.

Browser evidence records rendered HTML/CSS/JS checks. This build environment
blocks file-URL and localhost navigation, so actual browser navigation could
not be certified here. Local link paths and anchors were checked structurally;
the shipped markup uses ordinary relative assets/scripts and no fetch dependency.
See validation/browser-checks.json for the exact method and limitations.

DATA EDITING
HTML is a static published snapshot. Editing JSON does not automatically update
HTML tables or search data. Change matching reference pages and regenerate the
search index before distributing an edited version. Preserve stable IDs and
increment content versions when meanings change.

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

sources/data-model.schema.json is a generated language-neutral $defs bundle.
Select a named definition when validating; the bundle root is a catalog, not a
single gameplay payload. Enums with established values preserve their encodings.
x-members represents symbolic alternatives without inventing wire encodings.
Partially established enums expose only their established serialized subset.
Needs Decision means the schema covers only the supported portion. x-invariants
record semantic checks that a future server/content validator must enforce.
Neither a schema match nor Fully Defined certifies runtime bindings or balance.

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
links, the Data Inventory sidebar link, inventory-tagged search records,
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
