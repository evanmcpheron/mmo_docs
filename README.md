# Briarwake Development Guide

**Partial documentation edition — 9 October 2026.** This is an offline build manual, not a generated Unreal game. It contains initial implementation contracts and worked test specifications; it is not complete against the attached master prompt.

Extract the whole directory and open `index.html` in a desktop browser. Keep the folders together. The site is designed for offline use without a web server or CDN. URL-based browser verification was blocked by environment policy; isolated rendering/control checks are recorded separately. Browser storage is best effort; export checkmarks before moving the manual.

## Contents

349 HTML pages, 32 planned phases, 18 system chapters, 228 asset contracts (205 pre-existing and 23 faction-related additions), five vocation routes, six original region-family pages and 16 worked interaction examples. The register is intentionally non-exhaustive. Individual asset pages are initial contracts, not fully specified or compiled implementations.

## Destination and source boundaries

Authorized destination: `https://github.com/evanmcpheron/mmo_docs`. The original edition recorded 404/403 access failures; those are historical, not the current publication status. See `verification/faction-publication.json` for this task’s branch and PR record. Neither `Briarwake` nor `game_docs` is modified by this change.

The actual art ZIP, multiplayer-plugin ZIP, companion audit documents, installed Unreal Engine 5.8.3 and installed PaperZD were unavailable. Plugin findings are reported by the brief, not independently verified source findings. The original brief is retained unchanged; its tentative `RPG` name is superseded by **Briarwake**.

## Rebuild and validate

Python 3.10+ is sufficient for generation and static checks; no third-party Python packages are needed for them. On Windows, use `py -3` in place of `python3` when appropriate for the installed Python launcher.

```sh
python3 tools/build_manual_indexes.py
python3 tools/build_manual_indexes.py --check
python3 tools/validate_documentation.py
python3 tools/check_phase_integration.py
python3 tools/check_feature_coverage.py
python3 tools/simulate_population_scaling.py
python3 -m unittest discover -s tools/tests -v
```

`python3 tools/check_feature_coverage.py --require-complete` intentionally returns nonzero while the master acceptance conditions are incomplete. Do not weaken this check to make a partial delivery appear complete.

Optional browser QA uses Python Playwright and an installed Chromium executable: `python3 tools/browser_checks.py --chromium /usr/bin/chromium`. This is not required to read or rebuild the site. Both file and local-HTTP navigation were blocked in the delivery environment; `python3 tools/render_checks.py` performs narrower in-memory checks. These do not prove normal navigation, real storage persistence or file downloads.

Read `AGENTS.md` before editing. Current evidence is in `verification/`; source/access limitations and not-run game tests are in `sources/verification.json`. See `DELIVERY_STATUS.md` for unresolved work. No paid art, plugin source/binary, runtime C++, game assets or external font files are included.

## Faction allegiance and Hearthward campaign extension

Start at `design/factions-and-allegiance.html`, then `architecture/faction-contracts.html` and `walkthroughs/hearthward-campaign.html`. Four stable political allegiances are registered. Hearthward is the authored MVP selection; Briarbound, Ironfang and Tidebound remain locked pending real content. The Hollow Covenant is non-playable. Roadward Accord, Hearth Assembly and Veil Survey remain independent civic organizations.

The six Hearthward quests include dialogue, NPC/tile anchors, objective predicates and alternatives, exact reward sources, both permanent personal branches, a separately resolved public NorthRoad policy, neutral services, solo public work, and fenced Elderwood travel. Permanent faction/class and retained vocation-history rules are preserved. Phases00–31 stay intact: NPC13, board15 and SliceB19 remain; the full faction slice is26, not05.

`AGENTS.md` prohibits game runtime files in this repository. This extension therefore contains **no executable Unreal feature or production backend**. New native types are implementation contracts; SQLite fixtures exercise selected transaction semantics with trusted principals/evidence, not real clients, AI, compound clue evaluation or production persistence. Actual integration requires a separately authorized Briarwake change, its user-led C++ class-creation workflow, real assets and engine/backend tests. The unmerged game rename PR is a compatibility consideration, not a merged fact.

Authoritative faction inputs are `sources/factions.json`, `hearthward-campaign.json`, `faction-implementation.json`, the two `faction-*.schema.json` files, and the integration/acceptance/compatibility/traceability registries. The generator derives the faction pages, quest property values and **`sources/faction-localization.en.json`**; do not hand-edit that English export. The 72-requirement traceability page and 18-entry contradiction register identify scope, sources, phases, checks and runtime limitations.

```sh
python3 tools/validate_factions.py
python3 tools/validate_factions.py --deployment
```

The first checks authored contracts; the second must remain blocked while cooked-content and solo-runtime evidence is absent. This is separate from the unchanged full-guide `--require-complete` failure. Exact command outcomes and bounded browser evidence are in `verification/faction-checks.json`, `faction-test-output.txt`, `faction-render.json` and the two `faction-browser-*.json` reports. No 1–30-player runtime measurements are claimed.
