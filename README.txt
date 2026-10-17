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

DATA INVENTORY
Open guide/data-inventory.html or choose Data Inventory in the Catalogs sidebar.
Browse Enums, Interfaces and Schemas alphabetically; existing table filters and
global search also find inventory names. All links and content work offline.
Every associated feature page ends with Data, linking to stable inventory anchors.
New proposals contain names and metadata only, marked Pending Definition.
Existing formats and partial contracts remain in their original documentation.
Needs Review flags link to unresolved terminology and classification questions.

The authoritative registry is sources/data-inventory.json. It records structures,
page associations, section evidence, review questions and page-review coverage.
The 49 feature pages were reviewed alongside four reference/index pages. See the
inventory's Coverage section for every reviewed page and exclusion rationale.
No housing, territory, siege, authored geography or other deferred mechanics are
invented by the inventory. Coverage reflects the current documentation only.

Build: python3 scripts/build_data_inventory.py
Check without writing: python3 scripts/build_data_inventory.py --check
Focused consistency check: python3 validation/check_data_inventory.py
Inventory regression tests: python3 -m unittest discover -s validation -p 'test_*.py'
Full existing checks, including inventory: python3 validation/run_checks.py
All inventory commands require Python 3.10+ and the standard library only.
Optional rendered checks: node validation/check_inventory_browser.mjs
The optional browser check uses Node 22+ and an installed Chrome/Chromium, with
no downloaded packages. Set BRIARWAKE_CHROME_BIN if its path is not detected.
It writes validation/data-inventory-browser-checks.json; the original browser
evidence remains unchanged. It checks actual offline file navigation, filtering,
search, backlinks, mobile layout and reading with page JavaScript disabled.

The inventory builder owns guide/data-inventory.html, marked Data blocks,
Data links in page contents, the Data Inventory sidebar link, inventory-tagged
search records and documentation counts in data/manifest.json. Existing feature
HTML remains authoritative; no original full-site generator is included here.
The builder preserves the original feature text, catalogs, search records and
game-data definitions. It neither regenerates their tables nor executes gameplay.
Rebuilds replace owned output consistently and never add duplicate Data sections.

For additions, first read the feature text and existing inventory for shared
contracts. Edit the registry, keeping stable IDs, names and classifications.
Add each relevant feature page and its specific section to the entry's evidence;
feature_pages must match the HTML pages represented in that evidence. Choose a
canonical_page section from that evidence. Use Existing/Documented for existing
documented formats, or Proposed/Pending Definition for newly proposed contracts.
Catalog labels for previously unnamed formats do not rename original sources.
Do not add enum values, members, fields, types, constraints or implementation.
Attach unresolved questions through review_issues and Needs Review metadata.

When adding or changing feature text, review all affected associations first,
then record that completed review and rebuild with:
python3 scripts/build_data_inventory.py --review-page guide/example.html
Replace the example path with the actual page; the option is repeatable. A new
page is classified as Feature and must have supported inventory associations.
Reference/index exclusions instead need an explicit reason in registry.pages.
Checks detect new unreviewed pages, changed source text, stale section reviews,
duplicate names/IDs, missing files/anchors, missing associations, accidental
definitions, review-link inconsistencies and stale generated output. They cannot
replace a human feature review or establish that a proposed contract is balanced.

Actual definitions can later live on their canonical documentation pages while
the registry continues to catalog names and references. The inventory's basic
organization does not need to change when those definitions are authored.

SOURCES
Official research links are in guide/sources.html. The source archive checksum
is in data/provenance.json. Original attached files were left unchanged.
No branding or name in this reference has received a legal clearance review.
