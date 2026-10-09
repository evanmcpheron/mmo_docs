# Documentation workflow and authority

This repository documents the future game **Briarwake**. It does not contain a game implementation. The authorized destination is `evanmcpheron/mmo_docs`; never overwrite or publish changes to `evanmcpheron/game_docs` as a substitute.

## Canonical editing inputs

- `sources/manual-pages.json`: authored page prose and section records.
- `sources/current-asset-manifest.json`: provisional game-asset identity/path/type/ownership/creation/dependency contracts.
- `sources/phase-integration.json`: phase-specific creation, activation, wiring and acceptance recipes.
- `sources/feature-coverage.json`: preserved master requirement blocks and incomplete coverage mapping.
- System, vocation, region, reference and decision registries in `sources/` retain the associated contracts. Keep their relevant prose synchronized when editing the same decision.

Edit source JSON, not generated HTML or `site/search-data.js`. `build_manual_indexes.py` regenerates pages, asset identity/property/dependency tables, phase creation tables, asset/dependency indices, the page directory and offline search. Direct/reverse dependency edges and phase creation order must stay synchronized in the source registries; the validator rejects drift. Creation dependencies describe build prerequisites, not every later observer assignment.

Run the documented generation and validation commands from README. Review failures; do not suppress a validation rule to conceal an incomplete source audit or unsupported claim. Browser tests are a separate optional step. After editorial changes inspect rendered pages at desktop and narrow widths; static checks cannot establish visual quality or complete instructional depth.

## Evidence and design rules

Distinguish Committed requirement, Recommended initial choice, Tuning example, Deferred extension and Unverified integration. Exactly one primary vocation is required; combat discipline is independent. All essential PvE/region/profession progression must be achievable by one human. Do not add 3D art, platformer traversal, mandatory player services or mandatory parties.

One server/service authority owns each mutable fact. Definitions are immutable; Actors, UI and animation are projections. Transactions atomically record deductions, grants, unique domain outcomes and receipts. Zone transfers fence the source and admit one destination owner. A session menu does not provide persistence.

The source art/plugin ZIPs were not available for this edition. Do not turn brief-reported issues into line-verified findings without reading the actual source. Never mark Unreal compile, Blueprint compile, packaging or game/network/runtime tests as passed unless executed and recorded.

Keep user ZIPs, licensed previews, third-party source/binaries, credentials and game runtime files outside the documentation repository. Do not declare a redistribution license on behalf of third-party authors. Preserve `MASTER_PROMPT.original.md` unchanged and record explicit superseding decisions separately.

## Completion

This is a partial manual. Source-block accounting is not exhaustive atomic-feature coverage; initial asset contracts are not complete per-property implementation pages. Use strict coverage mode to expose remaining work. Record the actual scope of each later batch before changing maturity labels.
