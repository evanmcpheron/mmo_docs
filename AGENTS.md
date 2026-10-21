# Briarwake documentation repository

This repository is the gameplay design, data-contract and development-roadmap reference for a **planned** Unreal Engine 5 **native C++** MMORPG. No Unreal Engine project, implementation source repository, built client/server, integrated replication plugin, or runtime evidence exists yet.

## Repository ownership

- Edit only this documentation repository. Never infer a sibling game checkout or an implementation repository URL.
- `sources/development-roadmap.json` owns epics, dependencies, acceptance criteria, status and implementation evidence. `scripts/build_development_roadmap.py` owns its generated HTML.
- `sources/data-inventory.json` owns canonical gameplay schemas, enums, interfaces and review fingerprints. `scripts/build_data_inventory.py` owns inventory sections, search, navigation, schema outputs and manifest.
- Change canonical sources before rebuilding generated files; commit source and generated outputs together. Maintain existing IDs, AC anchors, links, gameplay semantics and approved visual direction.
- Unreal Engine 5 C++ is the initial technical foundation. No prior game implementation or runtime results may be treated as existing work.

## Future game implementation boundary

- Use Unreal Engine 5 native C++ for authoritative gameplay when the separate project is created; Blueprint may supplement assets and presentation.
- Verify and pin the engine release, compiler, target platforms and dedicated server build configuration before implementation.
- The owner has replication plugins available, but their names, versions, licenses, compatibility and coverage are unknown. Do not assume installation or invent capabilities. Evaluate built-in Unreal replication and actual plugins before proposing custom infrastructure.
- Ticket decomposition is allowed now. Running an implementation ticket requires a real game repository explicitly supplied or verified, project instructions and executed game tests. No game epic or ticket can be marked Complete based on documentation checks.

## Engineering standards

Follow the existing Python, HTML and JSON conventions. Keep code readable, maintainable, DRY when useful and limited to the requested scope. Avoid unnecessary frameworks, unrelated gameplay revisions or new dependencies. Do not fabricate technical citations, game tests, completion evidence, plugins or filesystem paths.

## Required checks after relevant changes

```sh
python3 scripts/build_development_roadmap.py
python3 scripts/build_data_inventory.py --review-roadmap
python3 scripts/build_development_roadmap.py --check
python3 scripts/build_data_inventory.py --check
python3 validation/check_development_roadmap.py
python3 validation/check_data_inventory.py
python3 -m unittest discover -s validation -p 'test_*.py'
python3 validation/run_checks.py
```

When authored chapter content changes, refresh its review fingerprint with `--review-page PATH` on the data inventory builder. For browser behavior run `node validation/check_inventory_browser.mjs` with Node 22+ and installed Chrome/Chromium. A documentation test result never constitutes gameplay runtime evidence.
