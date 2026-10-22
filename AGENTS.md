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
- Before any epic decomposition, follow the mandatory reuse assessment in `sources/development-roadmap.json` under `maintenance`, published at `guide/roadmap-maintenance.html`. This applies even when a workspace skill initiates the split. Inspect relevant engine/plugin implementation, project owners, completed dependencies and retained evidence before proposing additional work. The dated multiplayer assessment on that page is a starting point to recheck, not proof of current integration.
- Ticket decomposition is allowed now. Running an implementation ticket requires a real game repository explicitly supplied or verified, project instructions and executed game tests. No game epic or ticket can be marked Complete based on documentation checks.

## Engineering standards

Follow the existing Python, HTML and JSON conventions. Keep code readable, maintainable, DRY when useful and limited to the requested scope. Avoid unnecessary frameworks, unrelated gameplay revisions or new dependencies. Do not fabricate technical citations, game tests, completion evidence, plugins or filesystem paths.

## Development and validation

Read the task, canonical sources and directly relevant code/tests first; follow dependencies when needed instead of repeatedly scanning generated chapters. Work in small coherent increments. Preserve acceptance criteria, security checks, engineering standards and truthful evidence.

Ticket scopes must identify reusable owners, genuinely new work and evidence gaps; exact `epic_criteria` links must collectively cover every parent criterion. Reuse never removes authorization, sequencing, idempotency or recipient privacy gates. Keep all planning in the existing roadmap registry and use its current coverage/dependency/link/freshness checks; do not add a parallel registry or require game builds for routine ticket authoring.

During implementation, run FAST and correct failures with the smallest relevant command it reports. Regenerate affected outputs only after canonical sources change, using the commands in `README.txt`. FAST checks freshness without rebuilding or refreshing review fingerprints. Unknown files, shared infrastructure or uncertain dependency impact require FULL.

```sh
python3 validation/validate.py --mode fast
python3 validation/validate.py --mode full
```

FULL is the default and mandatory final PR gate, including browser tests with Node 22+ and installed Chrome/Chromium. Reuse successful results while their source dependencies, selected scope and toolchain remain unchanged; record the tested revision and local changes. Do not rerun it after every minor edit, claim comprehensive success from FAST, defer known defects, or fabricate evidence. CI always runs FULL, independently of changed-file selection. See `README.txt` for prerequisites, coverage, explicit evidence generation and focused commands. A documentation test result never constitutes gameplay runtime evidence.
