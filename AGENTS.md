# Briarwake documentation repository

This repository owns the gameplay design, data contracts and development roadmap for an Unreal Engine 5 **native C++** MMORPG. The separate game repository is https://github.com/evanmcpheron/BriarwakeUnreal. Retained, revision-specific implementation evidence is linked from the roadmap; documentation checks do not verify the current game checkout, engine, toolchain, plugins or runtime capabilities.

## Repository ownership

- Edit only this documentation repository unless the task explicitly authorizes game changes. Verify an actual game checkout and its instructions before implementation work.
- `sources/development-roadmap.json` owns epics, dependencies, acceptance criteria, status and implementation evidence. `scripts/build_development_roadmap.py` owns its generated HTML.
- `sources/data-inventory.json` owns canonical gameplay schemas, enums, interfaces and review fingerprints. `scripts/build_data_inventory.py` owns inventory sections, search, navigation, schema outputs and manifest.
- Change canonical sources before rebuilding generated files; commit source and generated outputs together. Maintain existing IDs, AC anchors, links, gameplay semantics and approved visual direction.
- Unreal Engine 5 C++ is the technical foundation. Reverify implementation and runtime claims against their recorded revisions and actual environment.

## Game implementation boundary

- Use Unreal Engine 5 native C++ for authoritative gameplay in the separate project; Blueprint may supplement assets and presentation.
- Verify and pin the engine release, compiler, target platforms and dedicated server build configuration before implementation.
- Before epic decomposition, use the focused reuse guidance in `sources/development-roadmap.json` under `maintenance`, published at `guide/roadmap-maintenance.html`. This applies even when a workspace skill initiates the split. Inspect relevant engine/plugin implementation, project owners, completed dependencies and retained evidence before proposing additional work. The dated multiplayer assessment on that page is a starting point to recheck, not proof of current integration.
- Ticket decomposition is allowed now. Running an implementation ticket requires a real game repository explicitly supplied or verified, project instructions and executed game tests. No game epic or ticket can be marked Complete based on documentation checks.

## Engineering standards

Follow the existing Python, HTML and JSON conventions. Keep code readable, maintainable, DRY when useful and limited to the requested scope. Avoid unnecessary frameworks, unrelated gameplay revisions or new dependencies. Do not fabricate technical citations, game tests, completion evidence, plugins or filesystem paths.

## Development and validation

[Validation policy](docs/validation.md) is the sole workflow authority. Read only
relevant sources/owners once, implement, use unit/static tests and required affected
generation, hand off concise human QA, update necessary tracking and open the PR.
A delivered PR can await QA while its ticket remains In Progress. Complete still
requires actual passing acceptance evidence; Not Run is explicitly unverified.

Use `python3 validation/validate.py --gate` once for affected PR source/freshness;
QUICK is for iteration. Do not repeat unchanged successful checks. A roadmap edit
uses only the roadmap generator; no inventory fingerprints, browser, allocation
suite or native execution. Follow the workspace Git/PR workflow when present.

AGENTS.md, docs/validation.md and workflow skills are protected from unrelated
feature edits. Increasing routine validation/budgets requires explicit workflow
authorization, the actual defect prevented, why a cheaper method is insufficient
and expected recurring cost. No automatic exhaustive visual testing, capture
frameworks, extra Unreal stages, unconditional packages/all-integration suites,
large evidence archives or unnecessary cross-repository administration. Stop after
sufficient checks and an honest manual QA handoff.
