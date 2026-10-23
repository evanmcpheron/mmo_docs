# Sufficient documentation verification

This is the sole documentation workflow policy. Read relevant canonical requirements
once, change necessary records, generate affected outputs once, verify and deliver.
Documentation checks never certify gameplay. PR readiness and accepted ticket
completion are separate: a code PR can await human QA with its ticket In Progress.

```sh
python3 validation/validate.py             # QUICK: affected source checks
python3 validation/validate.py --gate      # affected source + generated freshness
python3 validation/validate.py --explain
```

Run the gate once when delivering source/generated changes; a second QUICK is not
required. Routine roadmap edits check JSON, stable IDs, parent/AC/dependency links,
contract references, actual evidence/status structure and generated roadmap/search
freshness. They run no inventory generator, allocation suite, validator regression
suite, browser or Unreal process. Static links/anchors check public destinations.
Unknown inputs and failed Git detection remain reported; --gate exits 2 for
unresolved requirements, 1 for a failed executed check. Neither escalates to FULL.

Contract edits check the authoritative registry and its generated outputs. Shipped
data changes run relevant data invariants; allocation searches apply only to actual
allocation inputs. Python tooling changes select adjacent tests; explicitly add
relevant caller tests when behavior changes. No transitive import-analysis layer.
A content update never runs tests of its validator implementation.

## Generation and review

For roadmap/ticket/status changes use just:

```sh
python3 scripts/build_development_roadmap.py
python3 validation/validate.py --gate
```

This command owns roadmap HTML, its search records and necessary manifest counts;
it writes only changed files. Derived progress/readiness needs no manual dashboard/
phase/milestone audit. Generated roadmap pages are validated against their source,
not stored again as 160 reviewed-content fingerprints in the inventory registry.
No `--review-roadmap` or second generator is required. Preserve public anchors.

For actual contract/feature changes use `scripts/build_data_inventory.py`;
`--review-page PATH` records actual review of changed feature content/associations.
Do not refresh unrelated reviews to silence validation. Manually changed HTML uses
the pinned formatter on that file only. Node and installed pinned Prettier (`npm ci`
once per lockfile change) are required for generation/freshness; missing tools fail.

## Visual QA and tracking

Browser execution is only for changed browser/UI behavior. A generator code edit
that preserves output does not automatically require Chrome. Use a short human QA
handoff for affected UI: prerequisites/page, steps, expected/failure behavior and
cleanup. Record **Not Run — Manual QA Pending** until a person executes it. Codex
need not automate navigation, test multiple widths, restart an editor, make GIFs,
collect frames or build capture/report infrastructure. Specific quantitative ACs
still need suitable objective evidence. `--mode integration --gate` explicitly
runs the existing browser suite when justified; `--mode full` is exceptional,
comprehensive documentation regression, never a routine feature prerequisite.
Neither is selected automatically. Documentation cannot launch native builds.

The roadmap source owns status/evidence. Complete requires executed passing evidence
for every AC, complete dependencies and no current failure/pending evidence.
Implemented but unaccepted work remains In Progress; a real prerequisite may make
it Blocked. `verified_evidence.result` supports Not Run for an explicit gap; proposed
manual instructions are not a pass. Update parents only when relevant criteria
actually qualify. Do not lower ACs or falsify results for completion.

Only actual tracking/contracts/evidence changes require a docs edit/PR. Game code,
acceptance, ticket completion and publication need not happen in one operation.
A task explicitly executing a ticket updates that ticket once; an ordinary code
change may hand off results in its game PR. Do not repeat unchanged game checks.

## Evidence, stop rule and protected budget

When evidence is required, use one concise summary with tested revision/local input
identity, commands/results (Passed/Failed/Not Run), outstanding QA, limitations and
necessary durable links. A PR link can serve as the artifact. Keep all historical
accepted evidence/public links. No routine logs, captures, GIFs, frame CSVs, duplicate
native reports or review manifests in Git. Use ignored `artifacts/` for temporary
work; existing CI logs/artifact storage suffice for large necessary diagnostics.
Source plus changed-input digest identifies a check; no whole-site hash scan.

Prefer one deterministic unit test per responsibility; use integration only when a
real boundary cannot be established more cheaply. Once applicable checks pass and
manual QA is documented, stop. Rerun only for relevant input/environment/requirement
changes. Do not invent further audits or evidence work.

Plan about **5 minutes of routine automated verification**, excluding unavoidable
cold native compilation and explicit integration. QUICK <5s and routine docs gate
<15s are goals. If exceeded, identify the expensive stage, remove optional work,
preserve successful results and hand off missing required coverage honestly.
Never waive required compilation, authority/security checks or actual acceptance.

Ordinary feature work may not expand mandatory validation/budgets, add independent
engine stages, automate manual QA, require all integration, create evidence archives
or broaden cross-repository administration. Such a policy change requires explicit
authorization and a PR naming the defect prevented, cheaper alternatives and
expected recurring cost. Prefer deleting layers; add no generalized policy engine.
This policy, AGENTS.md and skill workflow standards are protected from unrelated
feature edits. See [audit and measurements](workflow-simplification.md).
