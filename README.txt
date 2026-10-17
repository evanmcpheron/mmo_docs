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
53 HTML pages: 21 system chapters, 12 class pages, 16 profession pages,
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

SOURCES
Official research links are in guide/sources.html. The source archive checksum
is in data/provenance.json. Original attached files were left unchanged.
No branding or name in this reference has received a legal clearance review.
