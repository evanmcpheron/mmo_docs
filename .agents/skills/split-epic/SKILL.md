---
name: split-epic
description: Split a Briarwake epic URL into tightly scoped tickets with acceptance criteria and manual tests, published in this documentation site.
---

# Split an epic

1. Read the supplied epic URL, its prerequisites, linked contracts and existing tickets. Use local sources when available. Inspect the Godot implementation in `../briarwake` so tickets reflect what actually exists.
2. If any epic specifics are ambiguous, missing or conflicting, ask the user to clarify instead of assuming. Wait for the answer before finalizing affected tickets; continue planning the clear, independent parts meanwhile.
3. Split the epic into small, independently verifiable behaviors in dependency order. Each ticket needs a title, parent epic link, exact epic AC links (`BW-NNN-AC-N`), scope boundaries, dependencies and observable acceptance criteria. Together, the tickets must cover every epic criterion. Preserve existing IDs and update existing tickets instead of duplicating them.
4. Where manual testing applies, include the scene or launch command, setup, actions, expected results and reset steps. Include necessary scene objects, fixtures, test data or controls in the ticket's implementation scope so execution leaves the test ready to run. Reuse existing test scenes where practical. Otherwise, state briefly why manual testing does not apply.
5. Store tickets in `sources/development-roadmap.json`, initially `Not Started`, using stable IDs such as `BW-001-T01`. Generate a page per ticket, linked both ways with its epic. Extend the existing builder and validator minimally if ticket support is missing; never hand-edit generated HTML.
6. Rebuild and run the relevant checks from `README.txt`, then return the ticket links in execution order. Planning alone does not complete the epic.
