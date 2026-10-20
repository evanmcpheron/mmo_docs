---
name: split-epic
description: Split a Briarwake roadmap epic into bounded implementation tickets grounded in the gameplay reference and Unreal C++ foundation.
---

# Split an epic

Read AGENTS.md and README.txt from this repository. Resolve the epic in sources/development-roadmap.json; inspect every criterion, dependency and related canonical contract. Read guide/unreal-cpp.html and guide/networking.html. No implementation location is designated; plan future behavior without asserting an existing codebase or naming nonexistent commands, classes or files as implemented.

Preserve the epic's responsibility and stable ID. Allocate unused BW-NNN-TNN IDs with one primary objective per ticket. Include parent_epic, exact epic_criteria anchors, dependencies, scope, exclusions, observable positive and failure acceptance criteria, required evidence, related_docs, and manual_test launch/setup/actions/expected_results/reset. Use clearly described future executable procedures until exact commands can be established; never invent executed results. Cover every parent criterion collectively, keep hard prerequisites distinct from recommendations, and avoid parallel definitions of gameplay rules. Treat owner-supplied replication plugins as awaiting verification.

All new tickets begin Not Started with empty verified_evidence and blockers unless an actual external blocker is identified. Planning does not advance implementation. Rebuild roadmap and inventory, run dependency/coverage/schema/link checks and review generated pages using README.txt. Follow the repository Git and PR workflow.
