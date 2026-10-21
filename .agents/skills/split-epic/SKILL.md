---
name: split-epic
description: Split a Briarwake Unreal Engine 5 C++ roadmap epic into narrowly scoped, testable planning tickets without assuming a game repository exists.
---

# Split an epic

1. Read the supplied epic, linked gameplay and data contracts, hard prerequisites, existing tickets, and repository instructions. This is the planning/documentation repository. The Unreal project and its separate implementation repository do not currently exist; do not inspect or invent one.
2. Clarify only decisions that materially change a ticket's contract. Distinguish confirmed requirements from future selections of the pinned Unreal Engine 5 revision, compiler/platform, and replication plugins.
3. Split the epic into small, independently demonstrable behaviors in dependency order. Give each ticket a stable ID, parent epic, exact `BW-NNN-AC-N` links, boundaries, dependencies, observable acceptance criteria, and evidence expectations. Preserve existing ticket and epic IDs; cover all parent criteria without duplication.
4. Where manual tests apply, specify their intended dedicated-server/client configuration, setup, actions, observations, negative cases and cleanup as **future instructions**. Do not invent build paths, engine commands, local environments or successful test results. Documentation-only tickets require documentation-appropriate verification.
5. Store ticket planning in `sources/development-roadmap.json` with `Not Started` status and no claimed implementation evidence. Use the existing generator and validators; only extend them if ticket support is actually required.
6. Rebuild, check links/search and report planning changes and generated ticket links. Splitting tickets is not implementation, and execution stays gated on the user providing a real game repository and verified project setup.
