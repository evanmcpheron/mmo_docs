---
name: split-epic
description: Split a Briarwake Unreal Engine 5 C++ roadmap epic into scoped, testable planning tickets grounded in verified implementation evidence.
---

# Split an epic

1. Read the supplied epic, directly linked gameplay/data contracts, hard prerequisites, existing tickets and repository instructions. This is the planning repository; the separate implementation is https://github.com/evanmcpheron/BriarwakeUnreal. Follow dependencies as needed and verify implementation claims against actual code or retained revision-specific evidence. Do not assume an installed engine, plugin capability or runnable system.
2. Apply the mandatory reuse assessment in `sources/development-roadmap.json` under `maintenance` (published in `guide/roadmap-maintenance.html`) before splitting. Record applicable source/version/configuration/test evidence, capability classifications, and the mapping from each parent AC to verified reuse, integration, missing behavior and required verification. Recheck the dated multiplayer assessment where relevant. Clarify only decisions that materially change a ticket's contract; unknown plugin behavior becomes bounded verification, never an implementation/completion claim.
3. Split the epic into small, independently demonstrable behaviors in dependency order. Give each ticket a stable ID, parent epic, exact `BW-NNN-AC-N` links, boundaries, dependencies, observable acceptance criteria, and evidence expectations. Preserve existing ticket and epic IDs; cover all parent criteria without duplication.
4. Where manual tests apply, specify their intended dedicated-server/client configuration, setup, actions, observations, negative cases and cleanup as **future instructions**. Do not invent build paths, engine commands, local environments or successful test results. Documentation-only tickets require documentation-appropriate verification.
5. Store ticket planning in `sources/development-roadmap.json` with `Not Started` status and no claimed implementation evidence. Use the existing generator and validators; only extend them if ticket support is actually required.
6. Follow the validation workflow in `AGENTS.md` and `README.txt`: regenerate affected outputs once after source changes, use FAST while correcting them and require FULL for final PR verification. Report planning changes and generated ticket links. Splitting tickets is not implementation; execution requires the verified game project setup and actual acceptance evidence.
